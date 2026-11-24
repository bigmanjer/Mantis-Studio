"use client";
import {
  ArrowDown,
  ArrowUp,
  BookMarked,
  Copy,
  FilePen,
  Lightbulb,
  Loader2,
  MessageCircleQuestion,
  Maximize2,
  Minimize2,
  PenLine,
  Plus,
  ScanSearch,
  Send,
  ShieldCheck,
  Sparkles,
  Trash2,
  Wand2,
  X,
} from "lucide-react";
import { useDeferredValue, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { mentionedIn } from "@/lib/world-context";
import { applyScan, parseScan, planIsEmpty, planScan, undoScan, type AppliedScan, type ScanPlan } from "./canonScan";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import { createClient } from "@/lib/supabase/client";
import { countWords, type Chapter, type Entity, type EntityCategory, type Project } from "@/lib/types";
import { AiClientError, runAi, streamAi } from "./aiClient";
import { SaveBadge, useAutosave } from "./autosave";
import VersionHistory from "./VersionHistory";

const PRESETS = ["Custom", "Improve Flow", "Fix Grammar", "Tighten", "Sensory Expansion", "Deepen POV", "Make Witty", "Make Darker", "Expand"];
const READ_WPM = 250;

interface Props {
  project: Project;
  chapters: Chapter[];
  setChapters: React.Dispatch<React.SetStateAction<Chapter[]>>;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
  setProject: React.Dispatch<React.SetStateAction<Project>>;
  aiContext: { project: object; entities: object[] };
  focus: boolean;
  setFocus: (f: boolean) => void;
}

export default function EditorTab({ project, chapters, setChapters, entities, setEntities, setProject, aiContext, focus, setFocus }: Props) {
  const supabase = createClient();
  const confirm = useConfirm();
  const [activeId, setActiveId] = useState(chapters[0]?.id ?? null);
  const active = chapters.find((c) => c.id === activeId) ?? null;

  useEffect(() => {
    if (!focus) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setFocus(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focus, setFocus]);

  function patchLocal(id: string, patch: Partial<Chapter>) {
    setChapters((prev) => prev.map((c) => (c.id === id ? { ...c, ...patch } : c)));
  }

  async function addChapter() {
    const position = chapters.length ? Math.max(...chapters.map((c) => c.position)) + 1 : 1;
    const { data, error } = await supabase
      .from("chapters")
      .insert({ project_id: project.id, user_id: project.user_id, position, title: `Chapter ${chapters.length + 1}` })
      .select("*")
      .single();
    if (!error && data) {
      setChapters((prev) => [...prev, data as Chapter]);
      setActiveId(data.id);
    }
  }

  async function move(id: string, dir: -1 | 1) {
    const sorted = [...chapters].sort((a, b) => a.position - b.position);
    const i = sorted.findIndex((c) => c.id === id);
    const j = i + dir;
    if (j < 0 || j >= sorted.length) return;
    const a = sorted[i];
    const b = sorted[j];
    setChapters((prev) => prev.map((c) => (c.id === a.id ? { ...c, position: b.position } : c.id === b.id ? { ...c, position: a.position } : c)));
    await Promise.all([
      supabase.from("chapters").update({ position: b.position }).eq("id", a.id),
      supabase.from("chapters").update({ position: a.position }).eq("id", b.id),
    ]);
  }

  async function remove(id: string) {
    const ch = chapters.find((c) => c.id === id);
    if (!ch) return;
    const ok = await confirm({
      title: `Delete “${ch.title || "Untitled"}”?`,
      body: `${ch.word_count.toLocaleString()} words will be permanently deleted. This can't be undone.`,
      confirmLabel: "Delete chapter",
      danger: true,
    });
    if (!ok) return;
    await supabase.from("chapters").delete().eq("id", id);
    const rest = chapters.filter((c) => c.id !== id);
    setChapters(rest);
    if (activeId === id) setActiveId(rest[0]?.id ?? null);
  }

  const sorted = [...chapters].sort((a, b) => a.position - b.position);
  const previousSummaries = active
    ? sorted.filter((c) => c.position < active.position && c.summary).map((c) => `${c.title}: ${c.summary}`)
    : [];

  return (
    <div className={`grid grid-cols-1 ${focus ? "" : "lg:grid-cols-[232px_minmax(0,1fr)_340px]"}`}>
      {/* Chapter list */}
      <aside className={`border-b border-line bg-panel/40 lg:sticky lg:top-[105px] lg:h-[calc(100vh-105px)] lg:overflow-y-auto lg:border-r lg:border-b-0 ${focus ? "hidden" : ""}`}>
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
          <p className="text-[11px] font-semibold tracking-widest text-muted uppercase">Chapters · {sorted.length}</p>
          <button onClick={addChapter} className="btn-quiet h-7 gap-1 px-2 text-xs" aria-label="Add chapter">
            <Plus size={14} /> Add
          </button>
        </div>
        <ol className="flex gap-1 overflow-x-auto px-2 pb-3 lg:block lg:space-y-0.5">
          {sorted.map((c, i) => {
            const isActive = c.id === activeId;
            return (
              <li key={c.id} className="group shrink-0">
                <div className={`flex items-center rounded-lg transition ${isActive ? "bg-panel-3" : "hover:bg-panel-2"}`}>
                  <button onClick={() => setActiveId(c.id)} className="flex min-w-0 flex-1 cursor-pointer items-start gap-2.5 px-2.5 py-2 text-left">
                    <span className={`mt-0.5 w-5 shrink-0 text-right text-[11px] tabular-nums ${isActive ? "text-accent" : "text-muted"}`}>{i + 1}</span>
                    <span className="min-w-0">
                      <span className={`block truncate text-sm ${isActive ? "font-medium text-text" : "text-muted"}`}>{c.title || "Untitled"}</span>
                      <span className="text-[11px] text-muted">{c.word_count ? `${c.word_count.toLocaleString()} words` : "Not started"}</span>
                    </span>
                  </button>
                  <div className={`shrink-0 items-center pr-1 text-muted ${isActive ? "flex" : "hidden group-hover:flex"}`}>
                    <button aria-label="Move chapter up" disabled={i === 0} onClick={() => move(c.id, -1)} className="cursor-pointer rounded p-1 hover:text-text disabled:opacity-30">
                      <ArrowUp size={13} />
                    </button>
                    <button aria-label="Move chapter down" disabled={i === sorted.length - 1} onClick={() => move(c.id, 1)} className="cursor-pointer rounded p-1 hover:text-text disabled:opacity-30">
                      <ArrowDown size={13} />
                    </button>
                    <button aria-label="Delete chapter" onClick={() => remove(c.id)} className="cursor-pointer rounded p-1 hover:text-danger">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </aside>

      {active ? (
        <ChapterEditor
          key={active.id}
          chapter={active}
          patchLocal={(p) => patchLocal(active.id, p)}
          focus={focus}
          setFocus={setFocus}
          project={project}
          entities={entities}
          setEntities={setEntities}
          setProject={setProject}
          aiContext={{ ...aiContext, chapterTitle: active.title, previousSummaries }}
        />
      ) : (
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 p-10 text-center lg:col-span-2">
          <PenLine size={28} className="text-accent" />
          <p className="font-serif text-xl font-semibold">No chapters yet</p>
          <p className="max-w-sm text-sm text-muted">Add a chapter to start writing, or build chapters from your outline in the Plan tab.</p>
          <button onClick={addChapter} className="btn-primary">
            <Plus size={16} /> Add your first chapter
          </button>
        </div>
      )}
    </div>
  );
}

type Issue = { problem: string; quote: string; canon: string; fix: string };
type AiMode = "draft" | "rewrite" | "canon" | "ask";
type Suggestion = { name: string; category: EntityCategory; description: string; aliases?: string[]; existingId?: string; newFacts?: string[]; newAliases?: string[] };
/** Word count each chapter had at its last canon scan (kept across chapter switches). */
const scannedWords = new Map<string, number>();
/** Projects whose empty planning fields were already auto-filled this session. */
const autoFilled = new Set<string>();

function ChapterEditor({
  chapter,
  patchLocal,
  project,
  entities,
  setEntities,
  setProject,
  aiContext,
  focus,
  setFocus,
}: {
  chapter: Chapter;
  patchLocal: (p: Partial<Chapter>) => void;
  project: Project;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
  setProject: React.Dispatch<React.SetStateAction<Project>>;
  aiContext: object;
  focus: boolean;
  setFocus: (f: boolean) => void;
}) {
  const supabase = createClient();
  const textRef = useRef<HTMLTextAreaElement>(null);
  // --- Version history + daily word log ---
  // The chapter as it was when opened, so the first save of a session can keep a "before" copy.
  const sessionStart = useRef({ title: chapter.title, content: chapter.content, words: chapter.word_count, saved: false });
  const lastSnapshotAt = useRef(Date.now());
  const loggedWords = useRef(chapter.word_count);
  const latest = useRef(chapter);
  latest.current = chapter;

  async function snapshot(title: string, content: string, words: number, reason: string) {
    if (!content.trim()) return;
    await supabase.from("chapter_versions").insert({
      chapter_id: chapter.id,
      project_id: project.id,
      user_id: project.user_id,
      title,
      content,
      word_count: words,
      reason,
    });
  }

  const localDay = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };

  const { state, schedule, flush } = useAutosave<Chapter>(async (patch) => {
    const now = new Date().toISOString();
    if ("content" in patch) {
      const s = sessionStart.current;
      if (!s.saved) {
        s.saved = true;
        await snapshot(s.title, s.content, s.words, "Before this session");
        lastSnapshotAt.current = Date.now();
      } else if (Date.now() - lastSnapshotAt.current > 10 * 60_000) {
        const c = latest.current;
        await snapshot(c.title, c.content, c.word_count, "Autosave");
        lastSnapshotAt.current = Date.now();
      }
    }
    const { error } = await supabase.from("chapters").update({ ...patch, updated_at: now }).eq("id", chapter.id);
    if (!error) {
      await supabase.from("projects").update({ updated_at: now }).eq("id", project.id);
      if (typeof patch.word_count === "number") {
        const delta = patch.word_count - loggedWords.current;
        loggedWords.current = patch.word_count;
        if (delta > 0) await supabase.rpc("log_words", { p_words: delta, p_day: localDay() });
      }
    }
    return { error };
  });

  async function restoreVersion(v: { title: string; content: string; word_count: number }) {
    await flush();
    const c = latest.current;
    await snapshot(c.title, c.content, c.word_count, "Before restore");
    loggedWords.current = v.word_count; // restoring isn't new writing
    set("title", v.title);
    set("content", v.content);
    await flush();
  }

  const [mode, setMode] = useState<AiMode>("draft");
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [needsKey, setNeedsKey] = useState(false);
  const [result, setResult] = useState<{
    kind: "continue" | "draft" | "rewrite" | "brainstorm" | "check";
    text: string;
    range?: [number, number];
  } | null>(null);
  // World Bible entries named in this chapter (deferred so typing stays smooth in long chapters).
  const deferredText = useDeferredValue(chapter.content);
  const inChapter = useMemo(() => mentionedIn(entities, deferredText), [entities, deferredText]);
  const resultRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (result) resultRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [result]);
  const [preset, setPreset] = useState(PRESETS[1]);
  const [customRewrite, setCustomRewrite] = useState("");
  const [issues, setIssues] = useState<Issue[] | null>(null);
  const [words, setWords] = useState(400);
  const [direction, setDirection] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [scanned, setScanned] = useState(false);
  const [pendingFacts, setPendingFacts] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [qa, setQa] = useState<{ q: string; a: string }[]>([]);

  // Let the manuscript grow like a page instead of scrolling inside a box.
  useLayoutEffect(() => {
    const el = textRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.max(el.scrollHeight, window.innerHeight * 0.6)}px`;
  }, [chapter.content, focus]);

  function set<K extends keyof Chapter>(key: K, value: Chapter[K]) {
    const patch: Partial<Chapter> = { [key]: value } as Partial<Chapter>;
    if (key === "content") patch.word_count = countWords(value as string);
    patchLocal(patch);
    schedule(patch);
  }

  // --- Automatic World Bible (original MANTIS "scan on save") ---
  // When the writer pauses after adding ~150 words, MANTIS reads the chapter and updates the World Bible,
  // the canon rules and the chapter summary by itself. Everything stays editable and one click undoes it.
  const autoOn = project.auto_canon !== false;
  const [autoLog, setAutoLog] = useState<AppliedScan | null>(null);
  const [autoState, setAutoState] = useState<"idle" | "scanning" | "error">("idle");
  const entitiesRef = useRef(entities);
  entitiesRef.current = entities;
  const projectRef = useRef(project);
  projectRef.current = project;
  if (!scannedWords.has(chapter.id)) scannedWords.set(chapter.id, chapter.summary.trim() ? chapter.word_count : 0);

  async function saveScan(plan: ScanPlan) {
    const p = projectRef.current;
    const applied = await applyScan(supabase, plan, { id: p.id, user_id: p.user_id, canon_rules: p.canon_rules }, { includeFacts: true });
    setEntities((prev) => {
      const next = prev.map((e) => {
        const m = plan.merges.find((x) => x.entity.id === e.id);
        return m && applied.updated.some((u) => u.id === e.id)
          ? { ...e, description: [e.description.trim(), ...m.newFacts.map((f) => `- ${f}`)].filter(Boolean).join("\n"), aliases: [...e.aliases, ...m.newAliases].slice(0, 30) }
          : e;
      });
      return [...next, ...applied.created];
    });
    if (applied.factsAdded.length) setProject((prev) => ({ ...prev, canon_rules: [prev.canon_rules.trim(), ...applied.factsAdded].filter(Boolean).join("\n") }));
    return applied;
  }

  async function autoScan() {
    const words = latest.current.word_count;
    scannedWords.set(chapter.id, words);
    setAutoState("scanning");
    try {
      const raw = await runAi({ action: "extract", text: latest.current.content, context: aiContext });
      const plan = planScan(parseScan(raw), entitiesRef.current, projectRef.current.canon_rules);
      if (plan.summary && !latest.current.summary.trim()) set("summary", plan.summary);
      if (!planIsEmpty(plan)) setAutoLog(await saveScan(plan));
      await autoFillPlan();
      setAutoState("idle");
    } catch {
      setAutoState("error");
    }
  }

  /** Once there's real writing, fill the book's empty planning fields (never overwrites the writer's text). */
  async function autoFillPlan() {
    const p = projectRef.current;
    const blank = (v: string | undefined) => !(v ?? "").trim();
    const titleBlank = blank(p.title) || /^untitled( project)?$/i.test(p.title.trim());
    if (autoFilled.has(p.id) || latest.current.word_count < 300) return;
    if (!titleBlank && !blank(p.genre) && !blank(p.premise) && !blank(p.style_guide)) return;
    autoFilled.add(p.id);
    const raw = await runAi({ action: "autofill", text: latest.current.content.slice(0, 6000), context: aiContext });
    const json = JSON.parse(raw.slice(raw.indexOf("{"), raw.lastIndexOf("}") + 1)) as Record<string, unknown>;
    const str = (v: unknown) => (Array.isArray(v) ? v.join("\n") : typeof v === "string" ? v.trim() : "");
    const patch: Partial<Project> = {};
    if (titleBlank && str(json.title)) patch.title = str(json.title).slice(0, 200);
    if (blank(p.genre) && str(json.genre)) patch.genre = str(json.genre).slice(0, 100);
    if (blank(p.premise) && str(json.premise)) patch.premise = str(json.premise).slice(0, 4000);
    if (blank(p.style_guide) && str(json.style_guide)) patch.style_guide = str(json.style_guide).slice(0, 4000);
    if (blank(projectRef.current.canon_rules) && str(json.canon_rules)) patch.canon_rules = str(json.canon_rules).slice(0, 4000);
    if (!Object.keys(patch).length) return;
    const { error } = await supabase.from("projects").update(patch).eq("id", p.id);
    if (!error) setProject((prev) => ({ ...prev, ...patch }));
  }

  useEffect(() => {
    if (!autoOn || busy) return;
    const since = chapter.word_count - (scannedWords.get(chapter.id) ?? 0);
    if (chapter.word_count < 120 || since < 150) return;
    const t = setTimeout(() => void autoScan(), 20_000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapter.content, autoOn, busy]);

  async function undoAuto() {
    if (!autoLog) return;
    await undoScan(supabase, autoLog, project.id);
    const created = new Set(autoLog.created.map((e) => e.id));
    setEntities((prev) =>
      prev.filter((e) => !created.has(e.id)).map((e) => {
        const u = autoLog.updated.find((x) => x.id === e.id);
        return u ? { ...e, description: u.description, aliases: u.aliases } : e;
      }),
    );
    if (autoLog.canonBefore !== null) setProject((prev) => ({ ...prev, canon_rules: autoLog.canonBefore ?? "" }));
    setAutoLog(null);
  }

  async function setAutoCanon(on: boolean) {
    setProject((prev) => ({ ...prev, auto_canon: on }));
    await supabase.from("projects").update({ auto_canon: on }).eq("id", project.id);
  }

  async function ai(label: string, fn: () => Promise<void>) {
    setBusy(label);
    setErr("");
    setNeedsKey(false);
    try {
      await fn();
    } catch (e) {
      setErr(e instanceof AiClientError ? e.message : "AI request failed.");
      setNeedsKey(e instanceof AiClientError && e.needsKey);
    } finally {
      setBusy(null);
    }
  }

  const selection = (): [number, number] | null => {
    const el = textRef.current;
    if (!el || el.selectionStart === el.selectionEnd) return null;
    return [el.selectionStart, el.selectionEnd];
  };

  const doContinue = () =>
    ai("continue", async () => {
      await streamAi({ action: "continue", text: chapter.content, words, instruction: direction, context: aiContext }, (text) =>
        setResult({ kind: "continue", text }),
      );
    });

  const doBrainstorm = () =>
    ai("brainstorm", async () => {
      await streamAi({ action: "brainstorm", text: chapter.content, instruction: direction, context: aiContext }, (text) =>
        setResult({ kind: "brainstorm", text }),
      );
    });

  const doRewrite = () => {
    const range = selection();
    if (!range) {
      setErr("Highlight a passage in the chapter first, then press Rewrite.");
      return;
    }
    return ai("rewrite", async () => {
      if (preset === "Custom" && !customRewrite.trim()) throw new AiClientError("Type how you want the passage rewritten first.");
      await streamAi(
        {
          action: "rewrite",
          text: chapter.content.slice(...range),
          preset: preset === "Custom" ? undefined : preset,
          instruction: preset === "Custom" ? customRewrite : undefined,
          context: aiContext,
        },
        (text) => setResult({ kind: "rewrite", text, range }),
      );
    });
  };

  const doDraftFromBeat = () =>
    ai("draft", async () => {
      await streamAi({ action: "draft", text: chapter.content, instruction: chapter.summary, words: 1200, context: aiContext }, (text) =>
        setResult({ kind: "draft", text }),
      );
    });

  const doCheck = () =>
    ai("check", async () => {
      const raw = await runAi({ action: "check", text: chapter.content, context: aiContext });
      let list: Issue[] = [];
      try {
        const parsed = JSON.parse(raw.slice(raw.indexOf("["), raw.lastIndexOf("]") + 1));
        list = (Array.isArray(parsed) ? parsed : [])
          .filter((i) => i && typeof i.problem === "string")
          .map((i) => ({ problem: String(i.problem), quote: String(i.quote ?? ""), canon: String(i.canon ?? ""), fix: String(i.fix ?? "") }));
      } catch {
        // Model didn't return JSON: show its text as a plain report instead.
        setResult({ kind: "check", text: raw });
        return;
      }
      setIssues(list);
    });

  /** Replace the quoted passage with the suggested fix. Refuses (rather than appending) if the quote isn't found. */
  function applyFix(i: Issue, idx: number) {
    const at = i.quote ? chapter.content.indexOf(i.quote) : -1;
    if (at < 0 || !i.fix) {
      setErr("Couldn't find that exact passage any more, so nothing was changed. Edit it by hand.");
      return;
    }
    void snapshot(chapter.title, chapter.content, chapter.word_count, "Before continuity fix");
    lastSnapshotAt.current = Date.now();
    set("content", chapter.content.slice(0, at) + i.fix + chapter.content.slice(at + i.quote.length));
    setIssues((prev) => (prev ? prev.filter((_, j) => j !== idx) : prev));
  }

  const doAsk = (e?: React.FormEvent, preset?: string) => {
    e?.preventDefault();
    const q = (preset ?? question).trim();
    if (!q || busy) return;
    return ai("ask", async () => {
      setQuestion("");
      setQa((prev) => [...prev, { q, a: "" }]);
      const update = (a: string) => setQa((prev) => prev.map((m, i) => (i === prev.length - 1 ? { q, a } : m)));
      try {
        await streamAi({ action: "ask", text: chapter.content, instruction: q, context: aiContext }, update);
      } catch (e) {
        setQa((prev) => prev.slice(0, -1));
        setQuestion(q);
        throw e;
      }
    });
  };

  const doSummarize = () =>
    ai("summarize", async () => {
      const text = await runAi({ action: "summarize", text: chapter.content });
      set("summary", text);
    });

  const doExtract = () =>
    ai("extract", async () => {
      const raw = await runAi({ action: "extract", text: chapter.content, context: aiContext });
      let plan: ScanPlan;
      try {
        plan = planScan(parseScan(raw), entities, project.canon_rules);
      } catch {
        throw new AiClientError("The AI returned something unreadable. Please try again.");
      }
      scannedWords.set(chapter.id, chapter.word_count);
      if (plan.summary && !chapter.summary.trim()) set("summary", plan.summary);
      setPendingFacts(plan.facts);
      setSuggestions([
        ...plan.creates,
        ...plan.merges.map((m) => ({
          name: m.entity.name,
          category: m.entity.category,
          description: "",
          existingId: m.entity.id,
          newFacts: [...m.newFacts, ...m.newAliases.map((a) => `Also called "${a}"`)],
          newAliases: m.newAliases,
        })),
      ]);
      setScanned(true);
    });

  async function addFact(f: string) {
    const next = [project.canon_rules.trim(), f].filter(Boolean).join("\n");
    const { error } = await supabase.from("projects").update({ canon_rules: next }).eq("id", project.id);
    if (!error) {
      setProject((prev) => ({ ...prev, canon_rules: next }));
      setPendingFacts((list) => list.filter((x) => x !== f));
    }
  }

  async function addSuggestion(s: Suggestion) {
    if (s.existingId && s.newFacts) {
      const existing = entities.find((e) => e.id === s.existingId);
      if (!existing) return;
      const facts = s.newFacts.filter((f) => !f.startsWith("Also called "));
      const merged = [existing.description.trim(), ...facts.map((f) => `- ${f}`)].filter(Boolean).join("\n");
      const aliases = [...existing.aliases, ...(s.newAliases ?? [])].slice(0, 30);
      const { error } = await supabase.from("entities").update({ description: merged, aliases }).eq("id", existing.id);
      if (!error) {
        setEntities((prev) => prev.map((e) => (e.id === existing.id ? { ...e, description: merged, aliases } : e)));
        setSuggestions((list) => list.filter((x) => x !== s));
      }
      return;
    }
    const { data, error } = await supabase
      .from("entities")
      .insert({ project_id: project.id, user_id: project.user_id, name: s.name, category: s.category, description: s.description, aliases: s.aliases ?? [] })
      .select("*")
      .single();
    if (!error && data) {
      setEntities((prev) => [...prev, data as Entity]);
      setSuggestions((list) => list.filter((x) => x !== s));
    }
  }

  function applyResult(how: "append" | "replace" | "insert") {
    if (!result) return;
    // Keep a copy before any AI change, so it can always be undone from History.
    void snapshot(chapter.title, chapter.content, chapter.word_count, "Before AI edit");
    lastSnapshotAt.current = Date.now();
    if (result.kind === "continue" || result.kind === "draft") {
      // AI-written words don't count toward the writer's own daily goal.
      loggedWords.current += countWords(result.text);
    }
    let next = chapter.content;
    if (how === "replace" && result.range) next = next.slice(0, result.range[0]) + result.text + next.slice(result.range[1]);
    else if (how === "insert" && result.range) next = next.slice(0, result.range[1]) + "\n\n" + result.text + next.slice(result.range[1]);
    else next = next.replace(/\s*$/, "") + (next.trim() ? "\n\n" : "") + result.text;
    set("content", next);
    setResult(null);
  }

  const readMins = Math.max(1, Math.round(chapter.word_count / READ_WPM));

  return (
    <>
      {/* Manuscript */}
      <section className={`min-w-0 bg-paper ${focus ? "min-h-screen" : ""}`}>
        <div className={`mx-auto w-full max-w-[44rem] px-5 sm:px-10 ${focus ? "py-20" : "py-10"}`}>
          <input
            className="w-full bg-transparent font-serif text-3xl font-semibold tracking-tight outline-none placeholder:text-muted/50"
            value={chapter.title}
            placeholder="Chapter title"
            onChange={(e) => set("title", e.target.value)}
            aria-label="Chapter title"
          />
          <div className="mt-2 mb-8 h-px w-16 bg-accent/60" />
          <textarea
            ref={textRef}
            className="prose-editor block w-full resize-none overflow-hidden bg-transparent outline-none placeholder:text-muted/40"
            value={chapter.content}
            onChange={(e) => set("content", e.target.value)}
            placeholder="It was a dark and stormy night…"
            aria-label="Chapter text"
            spellCheck
          />
        </div>
        {/* Status bar */}
        <div
          className={`sticky bottom-0 flex items-center justify-between gap-3 border-t border-line bg-panel/90 px-5 py-2 text-xs text-muted backdrop-blur ${
            focus ? "opacity-0 transition-opacity hover:opacity-100" : ""
          }`}
        >
          <span>
            {chapter.word_count.toLocaleString()} words · {readMins} min read
          </span>
          <span className="flex items-center gap-4">
            <SaveBadge state={state} />
            <VersionHistory chapterId={chapter.id} onRestore={restoreVersion} />
            <button
              onClick={() => setFocus(!focus)}
              className="flex cursor-pointer items-center gap-1.5 hover:text-text"
              title={focus ? "Exit focus mode (Esc)" : "Focus mode: hide everything but the page"}
            >
              {focus ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
              {focus ? "Exit focus" : "Focus"}
            </button>
          </span>
        </div>
      </section>

      {/* AI panel */}
      <aside
        className={`border-t border-line bg-panel/40 lg:sticky lg:top-[105px] lg:h-[calc(100vh-105px)] lg:overflow-y-auto lg:border-t-0 lg:border-l ${focus ? "hidden" : ""}`}
      >
        <div className="p-4">
          <p className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles size={15} className="text-accent" /> AI co-writer
          </p>
          <div className="mt-3 grid grid-cols-4 rounded-lg border border-line bg-panel-2 p-0.5 text-xs" role="tablist">
            {(
              [
                ["draft", "Draft", PenLine],
                ["rewrite", "Rewrite", Wand2],
                ["canon", "Canon", BookMarked],
                ["ask", "Ask", MessageCircleQuestion],
              ] as const
            ).map(([id, label, Icon]) => (
              <button
                key={id}
                role="tab"
                aria-selected={mode === id}
                onClick={() => {
                  setMode(id);
                  setErr("");
                }}
                className={`flex cursor-pointer items-center justify-center gap-1.5 rounded-md py-1.5 transition ${
                  mode === id ? "bg-panel text-text shadow-sm" : "text-muted hover:text-text"
                }`}
              >
                <Icon size={13} /> {label}
              </button>
            ))}
          </div>

          {inChapter.length > 0 && (
            <div className="mt-3">
              <p className="mb-1 text-[11px] text-muted">In this chapter · the AI reads these first</p>
              <div className="flex flex-wrap gap-1">
                {inChapter.slice(0, 12).map((e) => (
                  <span key={e.id} title={e.description || e.category} className="rounded-full border border-line bg-panel px-2 py-0.5 text-[11px] text-text/80">
                    {e.name}
                  </span>
                ))}
                {inChapter.length > 12 && <span className="px-1 text-[11px] text-muted">+{inChapter.length - 12} more</span>}
              </div>
            </div>
          )}


          {(autoLog || autoState !== "idle") && (
            <div className="mt-3 rounded-lg border border-line bg-panel px-3 py-2 text-[11px] text-muted" aria-live="polite">
              {autoState === "scanning" ? (
                <span className="flex items-center gap-1.5">
                  <Loader2 size={11} className="animate-spin" /> Updating the World Bible from this chapter…
                </span>
              ) : autoState === "error" ? (
                <span>Couldn&apos;t update the World Bible automatically just now. It will try again as you write.</span>
              ) : autoLog ? (
                <>
                  <span className="text-text/80">World Bible updated automatically: </span>
                  {[
                    autoLog.created.length ? `added ${autoLog.created.map((e) => e.name).slice(0, 4).join(", ")}${autoLog.created.length > 4 ? ` +${autoLog.created.length - 4}` : ""}` : "",
                    autoLog.updated.length ? `new details for ${autoLog.updated.length} ${autoLog.updated.length === 1 ? "entry" : "entries"}` : "",
                    autoLog.factsAdded.length ? `${autoLog.factsAdded.length} canon ${autoLog.factsAdded.length === 1 ? "rule" : "rules"}` : "",
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                  .{" "}
                  <button onClick={undoAuto} className="cursor-pointer font-medium text-accent hover:underline">
                    Undo
                  </button>
                  <button onClick={() => setAutoLog(null)} className="ml-2 cursor-pointer hover:text-text" aria-label="Dismiss">
                    ✕
                  </button>
                </>
              ) : null}
            </div>
          )}

          <div className="mt-4 space-y-3">
            {mode === "draft" && (
              <>
                {chapter.summary.trim() && chapter.word_count < 150 && (
                  <div className="rounded-xl border border-accent/30 bg-accent-soft p-3">
                    <p className="text-[11px] font-semibold tracking-wide text-accent uppercase">Chapter beat</p>
                    <p className="mt-1 line-clamp-3 text-xs text-text/90">{chapter.summary}</p>
                    <button onClick={doDraftFromBeat} disabled={!!busy} className="btn-primary mt-3 w-full">
                      {busy === "draft" ? <Loader2 size={15} className="animate-spin" /> : <FilePen size={15} />}
                      {busy === "draft" ? "Drafting the chapter…" : "Draft this chapter from its beat"}
                    </button>
                  </div>
                )}
                <textarea
                  rows={3}
                  className="input"
                  placeholder="Optional direction, e.g. “She realises the key is a fake”"
                  value={direction}
                  onChange={(e) => setDirection(e.target.value)}
                />
                <div className="flex gap-2">
                  <button onClick={doContinue} disabled={!!busy} className="btn-primary flex-1">
                    {busy === "continue" ? <Loader2 size={15} className="animate-spin" /> : <PenLine size={15} />}
                    {busy === "continue" ? "Writing…" : "Continue the scene"}
                  </button>
                  <select className="input w-[104px] shrink-0 py-2" value={words} onChange={(e) => setWords(Number(e.target.value))} aria-label="Length">
                    {[200, 400, 800, 1200].map((n) => (
                      <option key={n} value={n}>
                        ~{n}w
                      </option>
                    ))}
                  </select>
                </div>
                <button onClick={doBrainstorm} disabled={!!busy} className="btn-ghost w-full">
                  {busy === "brainstorm" ? <Loader2 size={15} className="animate-spin" /> : <Lightbulb size={15} />}
                  Brainstorm what happens next
                </button>
              </>
            )}

            {mode === "rewrite" && (
              <>
                <p className="text-xs text-muted">Highlight a passage in the chapter, pick a style, then rewrite.</p>
                <div className="flex flex-wrap gap-1.5">
                  {PRESETS.map((p) => (
                    <button
                      key={p}
                      onClick={() => setPreset(p)}
                      className={`cursor-pointer rounded-full border px-2.5 py-1 text-xs transition ${
                        preset === p ? "border-accent bg-accent-soft text-accent" : "border-line text-muted hover:text-text"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                {preset === "Custom" && (
                  <textarea
                    rows={2}
                    className="input"
                    placeholder="e.g. “Make her angrier but keep it quiet” or “Rewrite as a letter”"
                    value={customRewrite}
                    onChange={(e) => setCustomRewrite(e.target.value)}
                    aria-label="Custom rewrite instruction"
                  />
                )}
                <button onClick={doRewrite} disabled={!!busy} className="btn-primary w-full">
                  {busy === "rewrite" ? <Loader2 size={15} className="animate-spin" /> : <Wand2 size={15} />}
                  Rewrite selection
                </button>
              </>
            )}

            {mode === "canon" && (
              <>
                <label className="flex cursor-pointer items-start gap-2 rounded-xl border border-line bg-panel p-3 text-xs">
                  <input type="checkbox" className="mt-0.5 accent-[var(--color-accent)]" checked={autoOn} onChange={(e) => void setAutoCanon(e.target.checked)} />
                  <span>
                    <span className="font-medium text-text">Keep the World Bible up to date automatically</span>
                    <span className="mt-0.5 block text-muted">
                      When you pause, MANTIS adds new characters, places and details, records firm facts as canon rules and fills in the chapter summary. You can edit or undo anything.
                    </span>
                  </span>
                </label>
                <div className="rounded-xl border border-line bg-panel p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">Chapter summary</p>
                    <button onClick={doSummarize} disabled={!!busy || !chapter.content.trim()} className="btn-quiet h-7 px-2 text-xs">
                      {busy === "summarize" ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />} Summarize
                    </button>
                  </div>
                  <p className="mt-0.5 text-[11px] text-muted">The AI reads this as “story so far” in later chapters.</p>
                  <textarea rows={4} className="input mt-2" value={chapter.summary} onChange={(e) => set("summary", e.target.value)} />
                </div>
                <button onClick={doCheck} disabled={!!busy || !chapter.content.trim()} className="btn-primary w-full">
                  {busy === "check" ? <Loader2 size={15} className="animate-spin" /> : <ShieldCheck size={15} />}
                  {busy === "check" ? "Checking continuity…" : "Check continuity"}
                </button>
                {issues && issues.length === 0 && (
                  <p className="rounded-lg border border-accent/30 bg-accent-soft px-3 py-2 text-center text-xs text-accent">
                    No continuity problems found in this chapter.
                  </p>
                )}
                {issues && issues.length > 0 && (
                  <ul className="space-y-2">
                    {issues.map((i, idx) => (
                      <li key={idx} className="rounded-xl border border-warning/30 bg-panel p-3 text-sm">
                        <p className="font-medium">{i.problem}</p>
                        {i.quote && <p className="mt-1.5 border-l-2 border-warning/60 pl-2 font-serif text-xs text-muted">“{i.quote}”</p>}
                        {i.canon && <p className="mt-1.5 text-xs text-muted">Canon: {i.canon}</p>}
                        {i.fix && (
                          <p className="mt-1.5 text-xs">
                            Suggested: <span className="font-serif text-accent">{i.fix}</span>
                          </p>
                        )}
                        <div className="mt-2 flex gap-2">
                          {i.fix && i.quote && (
                            <button onClick={() => applyFix(i, idx)} className="btn-primary h-7 px-2.5 text-xs">
                              Apply fix
                            </button>
                          )}
                          <button onClick={() => setIssues((prev) => (prev ? prev.filter((_, j) => j !== idx) : prev))} className="btn-quiet h-7 px-2.5 text-xs">
                            Ignore
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
                <button onClick={doExtract} disabled={!!busy || !chapter.content.trim()} className="btn-ghost w-full">
                  {busy === "extract" ? <Loader2 size={15} className="animate-spin" /> : <ScanSearch size={15} />}
                  Scan chapter for new canon
                </button>
                {scanned && suggestions.length === 0 && pendingFacts.length === 0 && <p className="text-center text-xs text-muted">Nothing new found. Your World Bible is up to date.</p>}
                {pendingFacts.length > 0 && (
                  <div className="rounded-xl border border-line bg-panel p-3">
                    <p className="mb-1.5 text-xs font-medium">New canon facts</p>
                    <ul className="space-y-1.5">
                      {pendingFacts.map((f) => (
                        <li key={f} className="flex items-start justify-between gap-2 text-xs text-muted">
                          <span>{f}</span>
                          <button onClick={() => addFact(f)} className="btn-quiet h-6 shrink-0 gap-1 px-2 text-xs text-accent">
                            <Plus size={12} /> Add
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {suggestions.length > 1 && (
                  <button
                    onClick={async () => {
                      for (const s of [...suggestions]) await addSuggestion(s);
                    }}
                    className="btn-ghost w-full py-1.5 text-xs"
                  >
                    <Plus size={13} /> Add all {suggestions.length} to the World Bible
                  </button>
                )}
                {suggestions.length > 0 && (
                  <ul className="space-y-2">
                    {suggestions.map((s) => (
                      <li key={s.name} className="rounded-xl border border-line bg-panel p-3 text-sm">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium">{s.name}</span>
                          <button onClick={() => addSuggestion(s)} className="btn-quiet h-6 gap-1 px-2 text-xs text-accent">
                            <Plus size={12} /> {s.existingId ? "Merge" : "Add"}
                          </button>
                        </div>
                        <p className="text-[11px] text-accent">{s.existingId ? `New details for an existing ${s.category.toLowerCase()}` : s.category}</p>
                        {s.newFacts ? (
                          <ul className="mt-1 list-disc pl-4 text-xs text-muted">
                            {s.newFacts.map((f) => (
                              <li key={f}>{f}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-1 text-xs text-muted">{s.description}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}

            {mode === "ask" && (
              <>
                <p className="text-xs text-muted">Ask anything about your book. Answers come from your outline, canon, World Bible and this chapter.</p>
                {qa.length === 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {["Who knows the secret so far?", "What do we know about the main character?", "Any loose threads to pay off?"].map((s) => (
                      <button key={s} onClick={() => doAsk(undefined, s)} disabled={!!busy} className="cursor-pointer rounded-full border border-line px-2.5 py-1 text-xs text-muted hover:text-text">
                        {s}
                      </button>
                    ))}
                  </div>
                )}
                {qa.length > 0 && (
                  <div className="space-y-3">
                    {qa.map((m, i) => (
                      <div key={i} className="space-y-1.5">
                        <p className="ml-6 rounded-xl rounded-br-sm bg-accent-soft px-3 py-2 text-sm">{m.q}</p>
                        <p className="mr-6 rounded-xl rounded-bl-sm border border-line bg-panel px-3 py-2 text-sm whitespace-pre-wrap text-text/90">{m.a}</p>
                      </div>
                    ))}
                  </div>
                )}
                <form onSubmit={doAsk} className="flex gap-2">
                  <input className="input" placeholder="Ask about your story…" value={question} onChange={(e) => setQuestion(e.target.value)} aria-label="Question" />
                  <button type="submit" disabled={!!busy || !question.trim()} className="btn-primary px-3" aria-label="Ask">
                    {busy === "ask" ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
                  </button>
                </form>
              </>
            )}

            {err && (
              <div role="alert" className="rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">
                {err}{" "}
                {needsKey && (
                  <a href="/app/settings#ai" className="font-medium underline">
                    Open settings
                  </a>
                )}
              </div>
            )}
          </div>
        </div>

        {result && (
          <div ref={resultRef} className="mx-4 mb-4 scroll-mb-4 overflow-hidden rounded-xl border border-accent/40 bg-panel shadow-glow">
            <div className="flex items-center justify-between border-b border-line px-3 py-2">
              <p className="flex items-center gap-1.5 text-xs font-semibold text-accent">
                {result.kind === "check" ? <ShieldCheck size={13} /> : <Sparkles size={13} />}
                {result.kind === "check" ? "Continuity report" : result.kind === "brainstorm" ? "Ideas" : "Suggestion"}
              </p>
              <button onClick={() => setResult(null)} className="btn-quiet h-6 w-6 p-0" aria-label="Discard suggestion">
                <X size={13} />
              </button>
            </div>
            <div className="flex flex-wrap gap-2 border-b border-line p-3">
              {result.kind === "rewrite" && (
                <>
                  <button onClick={() => applyResult("replace")} disabled={!!busy} className="btn-primary flex-1 py-1.5">
                    Replace
                  </button>
                  <button onClick={() => applyResult("insert")} disabled={!!busy} className="btn-ghost py-1.5">
                    Insert after
                  </button>
                </>
              )}
              {(result.kind === "continue" || result.kind === "draft") && (
                <button onClick={() => applyResult("append")} disabled={!!busy} className="btn-primary flex-1 py-1.5">
                  {busy ? "Writing…" : "Add to chapter"}
                </button>
              )}
              <button onClick={() => navigator.clipboard.writeText(result.text)} className="btn-ghost py-1.5" aria-label="Copy suggestion">
                <Copy size={14} />
              </button>
            </div>
            <div className="max-h-[45vh] overflow-y-auto px-3 py-3 font-serif text-[14px] leading-relaxed whitespace-pre-wrap">{result.text}</div>
          </div>
        )}
      </aside>
    </>
  );
}
