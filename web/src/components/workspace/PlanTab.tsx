"use client";
import { BookOpen, Feather, ListPlus, ListTree, Loader2, ScrollText, ShieldAlert, SlidersHorizontal, Sparkles, Trash2, type LucideIcon } from "lucide-react";
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

// Mirrors STYLE_DIALS in lib/ai.ts (kept here so this client file doesn't import server code).
const DIALS = [
  { key: "pace", label: "Pace", low: "slower, lingering", high: "faster, propulsive", lowShort: "Slow", highShort: "Fast" },
  { key: "interiority", label: "Interiority", low: "more external", high: "deeper in their head", lowShort: "Action", highShort: "Inner" },
  { key: "imagery", label: "Imagery", low: "plainer", high: "richer, more sensory", lowShort: "Spare", highShort: "Lush" },
  { key: "dialogue", label: "Dialogue", low: "more narration", high: "more dialogue", lowShort: "Narration", highShort: "Dialogue" },
  { key: "mood", label: "Mood", low: "lighter", high: "darker, tenser", lowShort: "Light", highShort: "Dark" },
];

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

  const hasChapterText = chapters.some((c) => c.content.trim().length > 200);

  /** Build an outline from chapters already written (original MANTIS "reverse engineer outline"). */
  async function outlineFromChapters() {
    setAiBusy(true);
    setAiErr("");
    try {
      const digest = chapters
        .slice()
        .sort((a, b) => a.position - b.position)
        .map((c, i) => `Chapter ${i + 1}: ${c.title}\n${c.summary || c.content.slice(0, 900)}`)
        .join("\n\n");
      const text = await runAi({ action: "reverse_outline", text: digest, context: aiContext });
      const current = latest.current.outline.trim();
      set("outline", current ? `${current}\n\n--- Outline from chapters ---\n${text}` : text);
    } catch (e) {
      setAiErr(e instanceof AiClientError ? e.message : "AI request failed.");
    }
    setAiBusy(false);
  }

  const [fillBusy, setFillBusy] = useState(false);
  const [fillMsg, setFillMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const isBlank = (k: "title" | "genre" | "premise" | "canon_rules" | "style_guide") => {
    const v = (latest.current[k] ?? "").trim();
    return !v || (k === "title" && /^untitled( project)?$/i.test(v));
  };
  const sampleText = chapters
    .slice()
    .sort((a, b) => a.position - b.position)
    .map((c) => c.content)
    .join("\n\n")
    .slice(0, 6000);
  const hasMaterial = !!(project.premise.trim() || project.outline.trim() || sampleText.trim() || !isBlank("title"));

  /** Fill only the empty planning fields from what the author already has (like the original MANTIS). */
  async function autofill() {
    setFillBusy(true);
    setFillMsg(null);
    try {
      const raw = await runAi({ action: "autofill", text: sampleText, context: aiContext });
      const json = JSON.parse(raw.slice(raw.indexOf("{"), raw.lastIndexOf("}") + 1)) as Record<string, unknown>;
      const filled: string[] = [];
      const fields = [
        ["title", "title"],
        ["genre", "genre"],
        ["premise", "premise"],
        ["canon_rules", "canon rules"],
        ["style_guide", "style guide"],
      ] as const;
      for (const [key, label] of fields) {
        const val = json[key];
        const text = Array.isArray(val) ? val.join("\n") : typeof val === "string" ? val.trim() : "";
        if (text && isBlank(key)) {
          set(key, text.slice(0, key === "title" ? 200 : 4000));
          filled.push(label);
        }
      }
      setFillMsg(
        filled.length
          ? { ok: true, text: `Filled in: ${filled.join(", ")}. Edit anything you like.` }
          : { ok: true, text: "Everything already had something in it, so nothing was changed." },
      );
    } catch (e) {
      setFillMsg({ ok: false, text: e instanceof AiClientError ? e.message : "The AI's answer couldn't be read. Please try again." });
    }
    setFillBusy(false);
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
      title: `Move “${project.title || "Untitled"}” to the Trash?`,
      body: "You can restore it, with every chapter and the World Bible, from the Trash for 30 days. After that it's deleted for good.",
      confirmLabel: "Move to Trash",
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
          <Panel
            icon={BookOpen}
            title="The basics"
            hint="Write a premise, a few paragraphs or an outline, then let AI fill in whatever is still empty."
            action={
              <button
                onClick={autofill}
                disabled={fillBusy || !hasMaterial}
                className="btn-ghost"
                title={hasMaterial ? "Fill empty fields with AI (never overwrites your text)" : "Add a premise, title, outline or some chapter text first"}
              >
                {fillBusy ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
                {fillBusy ? "Filling in…" : "Fill in with AI"}
              </button>
            }
          >
            {fillMsg && (
              <p
                className={`mb-4 rounded-lg border px-3 py-2 text-sm ${
                  fillMsg.ok ? "border-accent/30 bg-accent-soft text-accent" : "border-danger/30 bg-danger-soft text-danger"
                }`}
              >
                {fillMsg.text}
              </p>
            )}
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
                {hasChapterText && (
                  <button
                    onClick={outlineFromChapters}
                    disabled={aiBusy}
                    className="btn-ghost"
                    title="Build an outline from the chapters you've already written, plus ideas for what comes next"
                  >
                    <ListTree size={15} /> From my chapters
                  </button>
                )}
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
          <Panel icon={SlidersHorizontal} title="Style dials" hint="Nudge how the AI writes for this book. The middle means no preference.">
            <div className="space-y-4">
              {DIALS.map((d) => {
                const v = project.style_dials?.[d.key] ?? 50;
                return (
                  <div key={d.key}>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium">{d.label}</span>
                      <span className="text-muted">{v === 50 ? "no preference" : v > 50 ? d.high : d.low}</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={5}
                      value={v}
                      onChange={(e) => set("style_dials", { ...(project.style_dials ?? {}), [d.key]: Number(e.target.value) })}
                      className="mt-1 w-full accent-[var(--accent)]"
                      aria-label={d.label}
                    />
                    <div className="flex justify-between text-[10px] text-muted">
                      <span>{d.lowShort}</span>
                      <span>{d.highShort}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </Panel>
          <Panel icon={ScrollText} title="Project" hint="Books in the Trash can be restored for 30 days.">
            <button onClick={onDelete} disabled={deleting} className="btn-danger w-full">
              {deleting ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
              {deleting ? "Moving…" : "Move to Trash"}
            </button>
          </Panel>
        </aside>
      </div>
    </div>
  );
}
