"use server";

import { planFor } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";
import type { AuthorLens } from "@/data/knowledge-builtin";
import type { KnowledgeHit } from "@/lib/knowledge";

const MAX_BYTES = 4 * 1024 * 1024;

export interface KnowledgeDoc {
  id: string;
  project_id: string | null;
  title: string;
  category: string;
  word_count: number;
  created_at: string;
}

/** Add a reference document (any supported format, or pasted text) to the Knowledge Base. */
export async function addKnowledgeDoc(formData: FormData): Promise<{ error?: string; doc?: KnowledgeDoc }> {
  const { supabase, user } = await requireUser();
  if (!user) return { error: "Please log in." };
  const profile = await getProfile(user.id, user.email);
  const plan = planFor(profile);
  const { count } = await supabase.from("knowledge_docs").select("id", { count: "exact", head: true });
  if ((count ?? 0) >= plan.maxKnowledgeDocs) {
    return { error: `The ${plan.name} plan holds ${plan.maxKnowledgeDocs} of your own documents. Delete one or upgrade for more.` };
  }

  const scope = String(formData.get("scope") || "");
  const projectId = scope && scope !== "all" ? scope : null;
  const file = formData.get("file");
  const pasted = String(formData.get("text") || "").trim();
  let text = pasted;
  let title = String(formData.get("title") || "").trim().slice(0, 200);

  if (file instanceof File && file.size > 0) {
    if (file.size > MAX_BYTES) return { error: "That file is over 4 MB. Save it as .docx or plain text and try again." };
    const { extractText, IMPORT_EXTENSIONS } = await import("@/lib/extract-text");
    const ext = file.name.toLowerCase().split(".").pop() ?? "";
    if (!(IMPORT_EXTENSIONS as readonly string[]).includes(ext)) {
      return { error: "Add a Word, PDF, RTF, OpenDocument, EPUB, HTML, Markdown or text file." };
    }
    try {
      text = await extractText(file);
    } catch {
      return { error: "We couldn't read that file. Try saving it as .docx or plain text." };
    }
    title ||= file.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim().slice(0, 200);
  }
  text = text.replace(/^#\s+/gm, "").trim();
  if (!text) return { error: "Choose a file or paste some text first." };
  title ||= text.split("\n")[0].slice(0, 80) || "Untitled notes";

  const { chunkText, classifyText } = await import("@/lib/knowledge");
  const chunks = chunkText(text);
  const { data: doc, error } = await supabase
    .from("knowledge_docs")
    .insert({ user_id: user.id, project_id: projectId, title, category: classifyText(text), word_count: text.split(/\s+/).filter(Boolean).length })
    .select("id, project_id, title, category, word_count, created_at")
    .single();
  if (error || !doc) return { error: error?.message ?? "Couldn't save that document." };

  for (let i = 0; i < chunks.length; i += 200) {
    const rows = chunks.slice(i, i + 200).map((content, j) => ({ doc_id: doc.id, user_id: user.id, project_id: projectId, position: i + j, content }));
    const { error: chErr } = await supabase.from("knowledge_chunks").insert(rows);
    if (chErr) {
      await supabase.from("knowledge_docs").delete().eq("id", doc.id);
      return { error: "Saving failed partway through. Nothing was added; please try again." };
    }
  }
  return { doc: doc as KnowledgeDoc };
}

export async function deleteKnowledgeDoc(id: string): Promise<{ error?: string }> {
  const { supabase, user } = await requireUser();
  if (!user) return { error: "Please log in." };
  const { error } = await supabase.from("knowledge_docs").delete().eq("id", id);
  return error ? { error: error.message } : {};
}

/** Search the writer's documents and/or the built-in library. */
export async function searchKnowledge(projectId: string, query: string, where: "all" | "mine" | "builtin" = "all"): Promise<KnowledgeHit[]> {
  const { supabase, user } = await requireUser();
  if (!user || !query.trim()) return [];
  const { searchBuiltin, searchMine } = await import("@/lib/knowledge");
  const [mine, builtin] = await Promise.all([
    where === "builtin" ? Promise.resolve([]) : searchMine(supabase, projectId, query, 8),
    where === "mine" ? Promise.resolve([]) : Promise.resolve(searchBuiltin(query, 8)),
  ]);
  return [...mine, ...builtin];
}

/** All author style lenses, plus the ones that best fit this book. */
export async function getLenses(projectId: string): Promise<{ all: AuthorLens[]; suggested: (AuthorLens & { why: string[] })[] }> {
  const { supabase, user } = await requireUser();
  if (!user) return { all: [], suggested: [] };
  const [{ AUTHOR_LENSES }, { suggestLenses }] = await Promise.all([import("@/data/knowledge-builtin"), import("@/lib/knowledge")]);
  const [{ data: p }, { data: ch }] = await Promise.all([
    supabase.from("projects").select("genre, premise, style_guide, outline").eq("id", projectId).maybeSingle(),
    supabase.from("chapters").select("content").eq("project_id", projectId).order("position").limit(3),
  ]);
  const bookText = [p?.genre, p?.genre, p?.premise, p?.style_guide, (p?.outline ?? "").slice(0, 3000), ...(ch ?? []).map((c) => c.content.slice(0, 3000))].filter(Boolean).join("\n");
  return { all: AUTHOR_LENSES, suggested: suggestLenses(bookText) };
}
