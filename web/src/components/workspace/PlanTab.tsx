"use client";
import { BookOpen, Feather, ListPlus, ListTree, Loader2, ScrollText, ShieldAlert, Sparkles, Trash2, type LucideIcon } from "lucide-react";
import { useRef, useState, useTransition } from "react";
import { deleteProject } from "@/app/app/actions";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import { createClient } from "@/lib/supabase/client";
import type { Chapter, Project } from "@/lib/types";
import { AiClientError, runAi } from "./aiClient";
import { SaveBadge, useAutosave } from "./autosave";

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

function Panel({
  icon: Icon,
  title,
  hint,
  action,
  children,
}: {
  icon: LucideIcon;
  title: string;
  hint?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="card p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 font-semibold">
            <Icon size={16} className="text-accent" /> {title}
          </h2>
          {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
        </div>
        {action}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function PlanTab({ project, setProject, chapters, setChapters, aiContext, goToWrite }: Props) {
  const supabase = createClient();
  const confirm = useConfirm();
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
    const placeholder =
      chapters.length === 1 && !chapters[0].content.trim() && /^chapter 1$/i.test(chapters[0].title) ? chapters[0] : null;
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

  async function onDelete() {
    const ok = await confirm({
      title: `Delete “${project.title || "Untitled"}”?`,
      body: "This permanently deletes the project, every chapter and the World Bible. Export first if you want a copy. This can’t be undone.",
      confirmLabel: "Delete project",
      danger: true,
    });
    if (ok) startDelete(() => deleteProject(project.id));
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-semibold">Plan the book</h1>
          <p className="mt-1 text-sm text-muted">Everything on this page is shared with the AI, so it writes on-story.</p>
        </div>
        <SaveBadge state={state} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          <Panel icon={BookOpen} title="The basics">
            <div className="grid gap-4 sm:grid-cols-6">
              <div className="sm:col-span-4">
                <label className="label" htmlFor="p-title">
                  Title
                </label>
                <input id="p-title" className="input" value={project.title} onChange={(e) => set("title", e.target.value)} />
              </div>
              <div className="sm:col-span-2">
                <label className="label" htmlFor="p-genre">
                  Genre
                </label>
                <input id="p-genre" className="input" value={project.genre} onChange={(e) => set("genre", e.target.value)} />
              </div>
              <div className="sm:col-span-4">
                <label className="label" htmlFor="p-author">
                  Author / pen name
                </label>
                <input id="p-author" className="input" value={project.author} onChange={(e) => set("author", e.target.value)} />
              </div>
              <div className="sm:col-span-2">
                <label className="label" htmlFor="p-target">
                  Target words
                </label>
                <input
                  id="p-target"
                  type="number"
                  min={1000}
                  step={1000}
                  className="input"
                  value={project.target_words}
                  onChange={(e) => set("target_words", Math.max(1000, Number(e.target.value) || 80000))}
                />
              </div>
              <div className="sm:col-span-6">
                <label className="label" htmlFor="p-premise">
                  Premise
                </label>
                <textarea
                  id="p-premise"
                  rows={4}
                  className="input font-serif text-[15px] leading-relaxed"
                  value={project.premise}
                  placeholder="Who is the story about, what do they want, and what stands in the way?"
                  onChange={(e) => set("premise", e.target.value)}
                />
              </div>
            </div>
          </Panel>

          <Panel
            icon={ListTree}
            title="Outline"
            hint="One line per chapter, like “Chapter 1: Title — what happens”, so MANTIS can turn it into chapters."
            action={
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-xs text-muted">
                  Chapters
                  <input
                    type="number"
                    min={3}
                    max={60}
                    value={chapterCount}
                    onChange={(e) => setChapterCount(Number(e.target.value) || 20)}
                    className="input w-16 py-1.5"
                  />
                </label>
                <button
                  onClick={generateOutline}
                  disabled={aiBusy || !project.premise.trim()}
                  className="btn-ghost"
                  title={project.premise.trim() ? "Draft an outline from your premise" : "Write a premise first"}
                >
                  {aiBusy ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
                  {aiBusy ? "Drafting…" : "Draft with AI"}
                </button>
              </div>
            }
          >
            {aiErr && <p className="mb-3 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{aiErr}</p>}
            <textarea
              rows={18}
              className="input font-mono text-[13px] leading-relaxed"
              value={project.outline}
              onChange={(e) => set("outline", e.target.value)}
              placeholder={"Chapter 1: The Letter — Mara finds her mother’s unsent letter…\nChapter 2: …"}
            />
            {parsed.length > 0 && (
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-panel-2 px-4 py-3">
                <p className="text-sm text-muted">
                  {parsed.length} chapter{parsed.length === 1 ? "" : "s"} detected
                  {newFromOutline.length < parsed.length && ` · ${parsed.length - newFromOutline.length} already created`}
                </p>
                {newFromOutline.length > 0 && (
                  <button onClick={createChaptersFromOutline} disabled={creating} className="btn-primary">
                    {creating ? <Loader2 size={15} className="animate-spin" /> : <ListPlus size={15} />}
                    Create {newFromOutline.length} chapter{newFromOutline.length === 1 ? "" : "s"}
                  </button>
                )}
              </div>
            )}
          </Panel>
        </div>

        <aside className="space-y-6">
          <Panel icon={ShieldAlert} title="Canon rules" hint="Facts the AI must never contradict: magic rules, ages, timeline, who knows what.">
            <textarea
              rows={8}
              className="input"
              value={project.canon_rules}
              placeholder={"Magic costs a memory.\nMara is 27.\nThe war ended 12 years ago."}
              onChange={(e) => set("canon_rules", e.target.value)}
            />
          </Panel>
          <Panel icon={Feather} title="Style guide" hint="Voice, tense, POV and tone for anything the AI writes.">
            <textarea
              rows={6}
              className="input"
              value={project.style_guide}
              placeholder="Close third person, past tense. Spare, lyrical prose."
              onChange={(e) => set("style_guide", e.target.value)}
            />
          </Panel>
          <Panel icon={ScrollText} title="Project" hint="Deleting removes every chapter and World Bible entry.">
            <button onClick={onDelete} disabled={deleting} className="btn-danger w-full">
              {deleting ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
              {deleting ? "Deleting…" : "Delete project"}
            </button>
          </Panel>
        </aside>
      </div>
    </div>
  );
}
