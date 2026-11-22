import { readFile } from "fs/promises";
import { notFound } from "next/navigation";
import path from "path";

const DOCS = { terms: "terms.md", privacy: "privacy.md" } as const;

export function generateStaticParams() {
  return Object.keys(DOCS).map((doc) => ({ doc }));
}

const TITLES: Record<string, string> = { terms: "Terms of Service", privacy: "Privacy Policy" };

export async function generateMetadata({ params }: { params: Promise<{ doc: string }> }) {
  const { doc } = await params;
  return { title: TITLES[doc] ?? "Legal" };
}

function inline(text: string) {
  return text.split(/\*\*(.+?)\*\*/g).map((part, j) => (j % 2 ? <strong key={j} className="text-text">{part}</strong> : part));
}

/** Minimal Markdown: headings, bullet lists, paragraphs and **bold**. Headings are split from the text below them. */
function render(md: string) {
  const blocks: { kind: "h1" | "h2" | "ul" | "p"; lines: string[] }[] = [];
  for (const raw of md.replace(/^﻿/, "").split(/\r?\n/)) {
    const line = raw.trim();
    const last = blocks[blocks.length - 1];
    if (!line) {
      blocks.push({ kind: "p", lines: [] });
    } else if (line.startsWith("# ")) {
      blocks.push({ kind: "h1", lines: [line.slice(2)] });
    } else if (line.startsWith("## ")) {
      blocks.push({ kind: "h2", lines: [line.slice(3)] });
    } else if (line.startsWith("- ")) {
      if (last?.kind === "ul") last.lines.push(line.slice(2));
      else blocks.push({ kind: "ul", lines: [line.slice(2)] });
    } else if (last?.kind === "p") {
      last.lines.push(line);
    } else {
      blocks.push({ kind: "p", lines: [line] });
    }
  }
  return blocks
    .filter((b) => b.lines.length)
    .map((b, i) => {
      if (b.kind === "h1") return <h1 key={i} className="font-serif text-3xl font-semibold">{b.lines[0]}</h1>;
      if (b.kind === "h2") return <h2 key={i} className="pt-4 text-lg font-semibold">{b.lines[0]}</h2>;
      if (b.kind === "ul")
        return (
          <ul key={i} className="list-disc space-y-1 pl-6 text-muted">
            {b.lines.map((l, j) => (
              <li key={j}>{inline(l)}</li>
            ))}
          </ul>
        );
      return (
        <p key={i} className="text-muted">
          {inline(b.lines.join(" "))}
        </p>
      );
    });
}

export default async function LegalPage({ params }: { params: Promise<{ doc: string }> }) {
  const { doc } = await params;
  const file = DOCS[doc as keyof typeof DOCS];
  if (!file) notFound();
  const md = (await readFile(path.join(process.cwd(), "content", "legal", file), "utf8"))
    .replaceAll("{{SUPPORT_EMAIL}}", process.env.NEXT_PUBLIC_SUPPORT_EMAIL || "mantisstudio.app@gmail.com")
    .replaceAll("{{EFFECTIVE_DATE}}", process.env.NEXT_PUBLIC_LEGAL_EFFECTIVE_DATE || "the date you first use the Service");
  return (
    <article className="mx-auto max-w-3xl space-y-4 px-4 py-16 leading-relaxed sm:py-24">{render(md)}</article>
  );
}
