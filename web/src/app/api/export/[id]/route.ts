import { AlignmentType, Document, HeadingLevel, Packer, PageBreak, Paragraph, TextRun } from "docx";
import { NextResponse } from "next/server";
import { planFor } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";
import type { Chapter, Project } from "@/lib/types";

function safeName(s: string) {
  return (s || "manuscript").replace(/[^\w\- ]+/g, "").trim().replace(/\s+/g, "_").slice(0, 80) || "manuscript";
}

// Ebook export may fetch the cover and illustrations.
export const maxDuration = 60;

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Please log in." }, { status: 401 });

  const url = new URL(req.url);
  const format = url.searchParams.get("format") ?? "md";
  const withOutline = url.searchParams.get("outline") === "1";

  const [{ data: project }, { data: chapters }] = await Promise.all([
    supabase.from("projects").select("*").eq("id", id).maybeSingle(),
    supabase.from("chapters").select("*").eq("project_id", id).order("position"),
  ]);
  if (!project) return NextResponse.json({ error: "Not found" }, { status: 404 });
  const p = project as Project;
  const chs = (chapters ?? []) as Chapter[];
  const name = safeName(p.title);

  if (format === "json") {
    // Full backup: everything needed to restore or move the book (re-importable on the Projects page).
    const { data: entities } = await supabase.from("entities").select("name, category, description, aliases").eq("project_id", id);
    const backup = {
      mantis_web: 1,
      exported_at: new Date().toISOString(),
      project: {
        title: p.title,
        author: p.author,
        genre: p.genre,
        premise: p.premise,
        outline: p.outline,
        canon_rules: p.canon_rules,
        style_guide: p.style_guide,
        target_words: p.target_words,
        style_dials: (p as Project & { style_dials?: unknown }).style_dials ?? null,
      },
      chapters: chs.map((c) => ({ title: c.title, content: c.content, summary: c.summary, word_count: c.word_count })),
      entities: entities ?? [],
    };
    return new NextResponse(JSON.stringify(backup, null, 2), {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Disposition": `attachment; filename="${name}.mantis.json"`,
      },
    });
  }

  if (format === "docx") {
    const profile = await getProfile(user.id, user.email);
    if (!planFor(profile).docxExport) {
      return NextResponse.json({ error: "Word export is available on Pro and Studio." }, { status: 402 });
    }
    const body: Paragraph[] = [
      new Paragraph({ text: p.title, heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER }),
    ];
    if (p.author) body.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `by ${p.author}`, italics: true })] }));
    if (withOutline) {
      if (p.premise) body.push(new Paragraph({ text: "Premise", heading: HeadingLevel.HEADING_2 }), ...paras(p.premise));
      if (p.outline) body.push(new Paragraph({ text: "Outline", heading: HeadingLevel.HEADING_2 }), ...paras(p.outline));
    }
    for (const c of chs) {
      body.push(new Paragraph({ children: [new PageBreak()] }));
      body.push(new Paragraph({ text: c.title, heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER, spacing: { after: 400 } }));
      body.push(...paras(c.content, true));
    }
    const doc = new Document({
      creator: p.author || "MANTIS Studio",
      title: p.title,
      styles: { default: { document: { run: { font: "Times New Roman", size: 24 }, paragraph: { spacing: { line: 480 } } } } },
      sections: [{ children: body }],
    });
    const buf = await Packer.toBuffer(doc);
    return new NextResponse(new Uint8Array(buf), {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Content-Disposition": `attachment; filename="${name}.docx"`,
      },
    });
  }

  if (format === "epub") {
    // Ebook for Kindle (KDP accepts EPUB), Apple Books, Kobo and Google Play. Paid plans, like Word export.
    const profile = await getProfile(user.id, user.email);
    if (!planFor(profile).docxExport) {
      return NextResponse.json({ error: "Ebook export is available on Pro and Studio." }, { status: 402 });
    }
    const { buildEpub } = await import("@/lib/epub");
    // Book art: the chosen cover and each chapter's illustrations (fetched a few at a time).
    const { data: art } = await supabase
      .from("book_images")
      .select("id, user_id, kind, chapter_id, prompt, seed, width, height, caption")
      .eq("project_id", id)
      .order("created_at")
      .limit(40);
    const { savedImage } = await import("@/lib/art-store");
    const fetched = new Map<string, { bytes: ArrayBuffer; type: string; caption: string }>();
    const wanted = (art ?? []).filter((a) => a.kind === "illustration" || a.id === (p as Project & { cover_id?: string }).cover_id);
    for (let i = 0; i < wanted.length; i += 4) {
      await Promise.all(
        wanted.slice(i, i + 4).map(async (a) => {
          try {
            fetched.set(a.id, { ...(await savedImage(a)), caption: a.caption });
          } catch {
            // A picture that fails to load is left out rather than failing the whole export.
          }
        }),
      );
    }
    const coverId = (p as Project & { cover_id?: string }).cover_id;
    const bytes = await buildEpub({
      id: p.id,
      title: p.title || "Untitled",
      author: p.author,
      description: p.premise,
      cover: coverId ? fetched.get(coverId) : undefined,
      chapters: chs.map((c) => ({
        title: c.title,
        content: c.content,
        images: (art ?? []).filter((a) => a.kind === "illustration" && a.chapter_id === c.id).flatMap((a) => (fetched.has(a.id) ? [fetched.get(a.id)!] : [])),
      })),
    });
    return new NextResponse(bytes as BodyInit, {
      headers: {
        "Content-Type": "application/epub+zip",
        "Content-Disposition": `attachment; filename="${name}.epub"`,
      },
    });
  }

  const md = format === "md";
  const parts: string[] = [md ? `# ${p.title}` : p.title.toUpperCase()];
  if (p.author) parts.push(md ? `*by ${p.author}*` : `by ${p.author}`);
  if (withOutline) {
    if (p.premise) parts.push(md ? `## Premise\n\n${p.premise}` : `PREMISE\n\n${p.premise}`);
    if (p.outline) parts.push(md ? `## Outline\n\n${p.outline}` : `OUTLINE\n\n${p.outline}`);
  }
  for (const c of chs) parts.push(md ? `## ${c.title}\n\n${c.content}` : `\n\n${c.title.toUpperCase()}\n\n${c.content}`);
  return new NextResponse(parts.join("\n\n") + "\n", {
    headers: {
      "Content-Type": md ? "text/markdown; charset=utf-8" : "text/plain; charset=utf-8",
      "Content-Disposition": `attachment; filename="${name}.${md ? "md" : "txt"}"`,
    },
  });
}

function paras(text: string, indent = false): Paragraph[] {
  return text
    .split(/\n\s*\n|\r?\n/)
    .filter((t) => t.trim())
    .map((t) => new Paragraph({ children: [new TextRun(t.trim())], indent: indent ? { firstLine: 720 } : undefined }));
}
