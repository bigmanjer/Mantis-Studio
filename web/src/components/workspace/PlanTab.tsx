"use client";
import { useRef, useState, useTransition } from "react";
import { deleteProject } from "@/app/app/actions";
import { createClient } from "@/lib/supabase/client";
import type { Chapter, Project } from "@/lib/types";
import { AiClientError, runAi } from "./aiClient";
import { SaveBadge, useAutosave } from "./useAutosave";

interface Props {
  project: Project;
  setProject: React.Dispatch<React.SetStateAction<Project>>;
  chapters: Chapter[];
  setChapters: React.Dispatch<React.SetStateAction<Chapter[]>>;
  aiContext: unknown;
  goToWrite: () => void;
}

/** Parse "Chapter 3: Title — beat" lines from an outline. */
export function parseOutline(outline: string): { title: string; beat: string }[] {
  const out: { title: string; beat: string }[] = [];
  for (const line of outline.split(/\r?\n/)) {
    const m = line.match(/^\s*(?:#+\s*)?(?:chapter|ch\.?)\s*(\d+)\s*[:.\-–—]\s*(.+)$/i);
    if (!m) continue;
    const [title, ...rest] = m[2].split(/\s+[—–-]\s+/);
    out.push({ title: title.trim().replace(/\*+/g, ""), beat: rest.join(" — ").trim() });
  }
  return out;
}

export default function PlanTab({ project, setProject, chapters, setChapters, aiContext, goToWrite }: Props) {
  const supabase = createClient();
  const { state, schedule } = useAutosave<Project>(async (patch) => {
    const { error } = await supabase
      .from("projects")
      .update({ ...patch, updated_at: new Date().toISOString() })
      .eq("id", project.id);
    return { error };
  });
  const [aiBusy, setAiBusy] = useState(false);
  const [aiErr, setAiErr] = useState("");
  const [chapterCount, setChapterCount] = useState(20);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, startDelete] = useTransition();
  const [creating, setCreating] = useState(false);
  const latest = useRef(project);
  latest.current = project;

  function set<K extends keyof Project>(key: K, value: Project[K]) {
    setProject((prev) => ({ ...prev, [key]: value }));
    schedule({ [key]: value } as Partial<Project>);
  }

  async function generateOutline() {
    setAiBusy(true);
    setAiErr("");
    try {
      const text = await runAi({ action: "outline", words: chapterCount, context: aiContext });
      // Merge into the outline as it is now (the user may have kept typing while the AI worked).
      const current = latest.current.outline.trim();
      set("outline", current ? `${current}\n\n--- AI draft ---\n${text}` : text);
    } catch (e) {
      setAiErr(e instanceof AiClientError ? e.message : "AI request failed.");
    }
    setAiBusy(false);
  }

  const parsed = parseOutline(project.outline);
  const existingTitles = new Set(chapters.map((c) => c.title.toLowerCase()));
  const newFromOutline = parsed.filter((p) => !existingTitles.has(p.title.toLowerCase()));

  async function createChaptersFromOutline() {
    setCreating(true);
    const base = chapters.length ? Math.max(...chapters.map((c) => c.position)) : 0;
    // Replace a lone empty "Chapter 1" placeholder instead of keeping it around.
    const placeholder = chapters.length === 1 && !chapters[0].content.trim() && /^chapter 1$/i.test(chapters[0].title) ? chapters[0] : null;
    const rows = newFromOutline.map((p, i) => ({
      project_id: project.id,
      user_id: project.user_id,
      position: (placeholder ? 0 : base) + i + 1,
      title: p.title,
      summary: p.beat,
    }));
    const { data, error } = await supabase.from("chapters").insert(rows).select("*");
    if (!error && data) {
      if (placeholder) await supabase.from("chapters").delete().eq("id", placeholder.id);
      const kept = placeholder ? chapters.filter((c) => c.id !== placeholder.id) : chapters;
      setChapters([...kept, ...(data as Chapter[])].sort((a, b) => a.position - b.position));
      goToWrite();
    } else setAiErr(error?.message ?? "Could not create chapters.");
    setCreating(false);
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[1fr_320px]">
      <div className="space-y-6">
        <div className="flex justify-end">
          <SaveBadge state={state} />
        </div>
        <section className="card space-y-4 p-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="label">Title</label>
              <input className="input" value={project.title} onChange={(e) => set("title", e.target.value)} />
            </div>
            <div>
              <label className="label">Genre</label>
              <input className="input" value={project.genre} onChange={(e) => set("genre", e.target.value)} />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="label">Author / pen name</label>
              <input className="input" value={project.author} onChange={(e) => set("author", e.target.value)} />
            </div>
            <div>
              <label className="label">Target words</label>
              <input
                type="number"
                min={1000}
                step={1000}
                className="input"
                value={project.target_words}
                onChange={(e) => set("target_words", Math.max(1000, Number(e.target.value) || 80000))}
              />
            </div>
          </div>
          <div>
            <label className="label">Premise</label>
            <textarea
              rows={4}
              className="input"
              value={project.premise}
              placeholder="Who is the story about, what do they want, and what stands in the way?"
              onChange={(e) => set("premise", e.target.value)}
            />
          </div>
        </section>

        <section className="card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-semibold">Outline</h2>
            <div className="flex flex-wrap items-center gap-2">
              <label className="text-xs text-muted">
                Chapters
                <input
                  type="number"
                  min={3}
                  max={60}
                  value={chapterCount}
                  onChange={(e) => setChapterCount(Number(e.target.value) || 20)}
                  className="input ml-2 inline-block w-16 py-1"
                />
              </label>
              <button onClick={generateOutline} disabled={aiBusy || !project.premise.trim()} className="btn-ghost" title={project.premise.trim() ? "" : "Write a premise first"}>
                {aiBusy ? "Generating…" : "✨ Generate with AI"}
              </button>
            </div>
          </div>
          <p className="mt-1 text-xs text-muted">
            Use one line per chapter, like <code className="text-accent">Chapter 1: Title — what happens</code>, so MANTIS can turn it into chapters.
          </p>
          {aiErr && <p className="mt-2 text-sm text-danger">{aiErr}</p>}
          <textarea
            rows={18}
            className="input mt-3 font-mono text-[13px] leading-relaxed"
            value={project.outline}
            onChange={(e) => set("outline", e.target.value)}
            placeholder={"Chapter 1: The Letter — Mara finds her mother's unsent letter…\nChapter 2: …"}
          />
          {newFromOutline.length > 0 && (
            <button onClick={createChaptersFromOutline} disabled={creating} className="btn-primary mt-3">
              {creating ? "Creating…" : `Create ${newFromOutline.length} chapter${newFromOutline.length === 1 ? "" : "s"} from outline`}
            </button>
          )}
        </section>
      </div>

      <aside className="space-y-6">
        <section className="card p-5">
          <h2 className="font-semibold">Canon rules</h2>
          <p className="mt-1 text-xs text-muted">Facts the AI must never contradict (magic rules, ages, timeline…).</p>
          <textarea rows={7} className="input mt-3" value={project.canon_rules} onChange={(e) => set("canon_rules", e.target.value)} />
        </section>
        <section className="card p-5">
          <h2 className="font-semibold">Style guide</h2>
          <p className="mt-1 text-xs text-muted">Voice, tense, POV and tone for AI-written text.</p>
          <textarea
            rows={6}
            className="input mt-3"
            value={project.style_guide}
            placeholder="Close third person, past tense. Spare, lyrical prose."
            onChange={(e) => set("style_guide", e.target.value)}
          />
        </section>
        <section className="card p-5">
          <h2 className="font-semibold text-danger">Danger zone</h2>
          {!confirmDelete ? (
            <button onClick={() => setConfirmDelete(true)} className="btn-danger mt-3 w-full">
              Delete project
            </button>
          ) : (
            <div className="mt-3 space-y-2 text-sm">
              <p>This permanently deletes the project, all chapters and the World Bible. This can&apos;t be undone.</p>
              <div className="flex gap-2">
                <button onClick={() => startDelete(() => deleteProject(project.id))} disabled={deleting} className="btn-danger flex-1">
                  {deleting ? "Deleting…" : "Yes, delete"}
                </button>
                <button onClick={() => setConfirmDelete(false)} className="btn-ghost flex-1">
                  Cancel
                </button>
              </div>
            </div>
          )}
        </section>
      </aside>
    </div>
  );
}
