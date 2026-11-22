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
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import { createClient } from "@/lib/supabase/client";
import { countWords, type Chapter, type Entity, type EntityCategory, type Project } from "@/lib/types";
import { AiClientError, runAi } from "./aiClient";
import { SaveBadge, useAutosave } from "./autosave";

const PRESETS = ["Improve Flow", "Fix Grammar", "Tighten", "Sensory Expansion", "Deepen POV", "Make Witty", "Make Darker", "Expand"];
const READ_WPM = 250;

interface Props {
  project: Project;
  chapters: Chapter[];
  setChapters: React.Dispatch<React.SetStateAction<Chapter[]>>;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
  aiContext: { project: object; entities: object[] };
  focus: boolean;
  setFocus: (f: boolean) => void;
}

export default function EditorTab({ project, chapters, setChapters, entities, setEntities, aiContext, focus, setFocus }: Props) {
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

type AiMode = "draft" | "rewrite" | "canon" | "ask";
type Suggestion = { name: string; category: EntityCategory; description: string };

function ChapterEditor({
  chapter,
  patchLocal,
  project,
  entities,
  setEntities,
  aiContext,
  focus,
  setFocus,
}: {
  chapter: Chapter;
  patchLocal: (p: Partial<Chapter>) => void;
  project: Project;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
  aiContext: object;
  focus: boolean;
  setFocus: (f: boolean) => void;
}) {
  const supabase = createClient();
  const textRef = useRef<HTMLTextAreaElement>(null);
  const { state, schedule } = useAutosave<Chapter>(async (patch) => {
    const now = new Date().toISOString();
    const { error } = await supabase.from("chapters").update({ ...patch, updated_at: now }).eq("id", chapter.id);
    if (!error) await supabase.from("projects").update({ updated_at: now }).eq("id", project.id);
    return { error };
  });

  const [mode, setMode] = useState<AiMode>("draft");
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [needsKey, setNeedsKey] = useState(false);
  const [result, setResult] = useState<{
    kind: "continue" | "draft" | "rewrite" | "brainstorm" | "check";
    text: string;
    range?: [number, number];
  } | null>(null);
  const [preset, setPreset] = useState(PRESETS[0]);
  const [words, setWords] = useState(400);
  const [direction, setDirection] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [scanned, setScanned] = useState(false);
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
      const text = await runAi({ action: "continue", text: chapter.content, words, instruction: direction, context: aiContext });
      setResult({ kind: "continue", text });
    });

  const doBrainstorm = () =>
    ai("brainstorm", async () => {
      const text = await runAi({ action: "brainstorm", text: chapter.content, instruction: direction, context: aiContext });
      setResult({ kind: "brainstorm", text });
    });

  const doRewrite = () => {
    const range = selection();
    if (!range) {
      setErr("Highlight a passage in the chapter first, then press Rewrite.");
      return;
    }
    return ai("rewrite", async () => {
      const text = await runAi({ action: "rewrite", text: chapter.content.slice(...range), preset, context: aiContext });
      setResult({ kind: "rewrite", text, range });
    });
  };

  const doDraftFromBeat = () =>
    ai("draft", async () => {
      const text = await runAi({ action: "draft", text: chapter.content, instruction: chapter.summary, words: 1200, context: aiContext });
      setResult({ kind: "draft", text });
    });

  const doCheck = () =>
    ai("check", async () => {
      const text = await runAi({ action: "check", text: chapter.content, context: aiContext });
      setResult({ kind: "check", text });
    });

  const doAsk = (e: React.FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;
    return ai("ask", async () => {
      const a = await runAi({ action: "ask", text: chapter.content, instruction: q, context: aiContext });
      setQa((prev) => [...prev, { q, a }]);
      setQuestion("");
    });
  };

  const doSummarize = () =>
    ai("summarize", async () => {
      const text = await runAi({ action: "summarize", text: chapter.content });
      set("summary", text);
    });

  const doExtract = () =>
    ai("extract", async () => {
      const raw = await runAi({ action: "extract", text: chapter.content });
      let items: Suggestion[] = [];
      try {
        items = JSON.parse(raw.slice(raw.indexOf("["), raw.lastIndexOf("]") + 1));
      } catch {
        throw new AiClientError("The AI returned something unreadable. Please try again.");
      }
      const known = new Set(entities.map((e) => e.name.toLowerCase()));
      const cats = ["Character", "Location", "Item", "Faction", "Lore"];
      setSuggestions(items.filter((i) => i?.name && cats.includes(i.category) && !known.has(i.name.toLowerCase())));
      setScanned(true);
    });

  async function addSuggestion(s: Suggestion) {
    const { data, error } = await supabase
      .from("entities")
      .insert({ project_id: project.id, user_id: project.user_id, name: s.name, category: s.category, description: s.description })
      .select("*")
      .single();
    if (!error && data) {
      setEntities((prev) => [...prev, data as Entity]);
      setSuggestions((list) => list.filter((x) => x !== s));
    }
  }

  function applyResult(how: "append" | "replace" | "insert") {
    if (!result) return;
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
                  <select className="input w-[88px] py-2" value={words} onChange={(e) => setWords(Number(e.target.value))} aria-label="Length">
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
                <button onClick={doRewrite} disabled={!!busy} className="btn-primary w-full">
                  {busy === "rewrite" ? <Loader2 size={15} className="animate-spin" /> : <Wand2 size={15} />}
                  Rewrite selection
                </button>
              </>
            )}

            {mode === "canon" && (
              <>
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
                <button onClick={doExtract} disabled={!!busy || !chapter.content.trim()} className="btn-ghost w-full">
                  {busy === "extract" ? <Loader2 size={15} className="animate-spin" /> : <ScanSearch size={15} />}
                  Scan chapter for new canon
                </button>
                {scanned && suggestions.length === 0 && <p className="text-center text-xs text-muted">No new characters, places or lore found.</p>}
                {suggestions.length > 0 && (
                  <ul className="space-y-2">
                    {suggestions.map((s) => (
                      <li key={s.name} className="rounded-xl border border-line bg-panel p-3 text-sm">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium">{s.name}</span>
                          <button onClick={() => addSuggestion(s)} className="btn-quiet h-6 gap-1 px-2 text-xs text-accent">
                            <Plus size={12} /> Add
                          </button>
                        </div>
                        <p className="text-[11px] text-accent">{s.category}</p>
                        <p className="mt-1 text-xs text-muted">{s.description}</p>
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
                      <button key={s} onClick={() => setQuestion(s)} className="cursor-pointer rounded-full border border-line px-2.5 py-1 text-xs text-muted hover:text-text">
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
          <div className="mx-4 mb-4 overflow-hidden rounded-xl border border-accent/40 bg-panel shadow-glow">
            <div className="flex items-center justify-between border-b border-line px-3 py-2">
              <p className="flex items-center gap-1.5 text-xs font-semibold text-accent">
                {result.kind === "check" ? <ShieldCheck size={13} /> : <Sparkles size={13} />}
                {result.kind === "check" ? "Continuity report" : result.kind === "brainstorm" ? "Ideas" : "Suggestion"}
              </p>
              <button onClick={() => setResult(null)} className="btn-quiet h-6 w-6 p-0" aria-label="Discard suggestion">
                <X size={13} />
              </button>
            </div>
            <div className="max-h-80 overflow-y-auto px-3 py-3 font-serif text-[14px] leading-relaxed whitespace-pre-wrap">{result.text}</div>
            <div className="flex flex-wrap gap-2 border-t border-line p-3">
              {result.kind === "rewrite" && (
                <>
                  <button onClick={() => applyResult("replace")} className="btn-primary flex-1 py-1.5">
                    Replace
                  </button>
                  <button onClick={() => applyResult("insert")} className="btn-ghost py-1.5">
                    Insert after
                  </button>
                </>
              )}
              {(result.kind === "continue" || result.kind === "draft") && (
                <button onClick={() => applyResult("append")} className="btn-primary flex-1 py-1.5">
                  Add to chapter
                </button>
              )}
              <button onClick={() => navigator.clipboard.writeText(result.text)} className="btn-ghost py-1.5" aria-label="Copy suggestion">
                <Copy size={14} />
              </button>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
