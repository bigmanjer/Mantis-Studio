"use client";
import { useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { countWords, type Chapter, type Entity, type EntityCategory, type Project } from "@/lib/types";
import { AiClientError, runAi } from "./aiClient";
import { SaveBadge, useAutosave } from "./useAutosave";

const PRESETS = ["Fix Grammar", "Improve Flow", "Tighten", "Sensory Expansion", "Deepen POV", "Make Witty", "Make Darker", "Expand"];

interface Props {
  project: Project;
  chapters: Chapter[];
  setChapters: React.Dispatch<React.SetStateAction<Chapter[]>>;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
  aiContext: { project: object; entities: object[] };
}

export default function EditorTab({ project, chapters, setChapters, entities, setEntities, aiContext }: Props) {
  const supabase = createClient();
  const [activeId, setActiveId] = useState(chapters[0]?.id ?? null);
  const [focus, setFocus] = useState(false);
  const active = chapters.find((c) => c.id === activeId) ?? null;

  function patchLocal(id: string, patch: Partial<Chapter>) {
    setChapters((prev) => prev.map((c) => (c.id === id ? { ...c, ...patch } : c)));
  }

  async function addChapter() {
    const position = chapters.length ? Math.max(...chapters.map((c) => c.position)) + 1 : 1;
    const { data, error } = await supabase
      .from("chapters")
      .insert({ project_id: project.id, user_id: project.user_id, position, title: `Chapter ${position}` })
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
    const next = chapters.map((c) => (c.id === a.id ? { ...c, position: b.position } : c.id === b.id ? { ...c, position: a.position } : c));
    setChapters(next);
    await Promise.all([
      supabase.from("chapters").update({ position: b.position }).eq("id", a.id),
      supabase.from("chapters").update({ position: a.position }).eq("id", b.id),
    ]);
  }

  async function remove(id: string) {
    const ch = chapters.find((c) => c.id === id);
    if (!ch) return;
    if (!window.confirm(`Delete "${ch.title}"? This can't be undone.`)) return;
    await supabase.from("chapters").delete().eq("id", id);
    const rest = chapters.filter((c) => c.id !== id);
    setChapters(rest);
    if (activeId === id) setActiveId(rest[0]?.id ?? null);
  }

  const sorted = [...chapters].sort((a, b) => a.position - b.position);
  const previousSummaries = active ? sorted.filter((c) => c.position < active.position && c.summary).map((c) => `${c.title}: ${c.summary}`) : [];

  return (
    <div className={`grid min-h-[calc(100vh-9rem)] ${focus ? "" : "lg:grid-cols-[220px_1fr_320px]"}`}>
      <aside className={`border-b border-line p-3 lg:border-r lg:border-b-0 ${focus ? "hidden" : ""}`}>
        <div className="mb-2 flex items-center justify-between px-1">
          <p className="text-xs font-medium tracking-wide text-muted uppercase">Chapters</p>
          <button onClick={addChapter} className="cursor-pointer text-sm text-accent hover:underline">
            + Add
          </button>
        </div>
        <ul className="flex gap-1 overflow-x-auto lg:block lg:space-y-0.5">
          {sorted.map((c, i) => (
            <li key={c.id} className="group shrink-0">
              <div className={`flex items-center rounded-lg ${c.id === activeId ? "bg-panel-2" : "hover:bg-panel-2/60"}`}>
                <button onClick={() => setActiveId(c.id)} className="min-w-0 flex-1 cursor-pointer px-2 py-1.5 text-left">
                  <p className={`truncate text-sm ${c.id === activeId ? "text-text" : "text-muted"}`}>{c.title || "Untitled"}</p>
                  <p className="text-[11px] text-muted">{c.word_count.toLocaleString()} words</p>
                </button>
                <div className={`shrink-0 pr-1 text-xs text-muted ${c.id === activeId ? "flex" : "hidden group-hover:flex"}`}>
                  <button aria-label="Move up" disabled={i === 0} onClick={() => move(c.id, -1)} className="cursor-pointer px-1 hover:text-text disabled:opacity-30">
                    ↑
                  </button>
                  <button aria-label="Move down" disabled={i === sorted.length - 1} onClick={() => move(c.id, 1)} className="cursor-pointer px-1 hover:text-text disabled:opacity-30">
                    ↓
                  </button>
                  <button aria-label="Delete chapter" onClick={() => remove(c.id)} className="cursor-pointer px-1 hover:text-danger">
                    ✕
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
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
        <div className="flex items-center justify-center p-10 text-muted lg:col-span-2">
          <button onClick={addChapter} className="btn-primary">
            Add your first chapter
          </button>
        </div>
      )}
    </div>
  );
}

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
  focus: boolean;
  setFocus: (f: boolean) => void;
  chapter: Chapter;
  patchLocal: (p: Partial<Chapter>) => void;
  project: Project;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
  aiContext: object;
}) {
  const supabase = createClient();
  const textRef = useRef<HTMLTextAreaElement>(null);
  const { state, schedule } = useAutosave<Chapter>(async (patch) => {
    const now = new Date().toISOString();
    const { error } = await supabase.from("chapters").update({ ...patch, updated_at: now }).eq("id", chapter.id);
    if (!error) await supabase.from("projects").update({ updated_at: now }).eq("id", project.id);
    return { error };
  });

  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [needsKey, setNeedsKey] = useState(false);
  const [result, setResult] = useState<{ kind: "continue" | "rewrite" | "brainstorm"; text: string; range?: [number, number] } | null>(null);
  const [preset, setPreset] = useState(PRESETS[1]);
  const [words, setWords] = useState(400);
  const [direction, setDirection] = useState("");
  const [suggestions, setSuggestions] = useState<{ name: string; category: EntityCategory; description: string }[]>([]);

  function set<K extends keyof Chapter>(key: K, value: Chapter[K]) {
    const patch: Partial<Chapter> = { [key]: value } as Partial<Chapter>;
    if (key === "content") patch.word_count = countWords(value as string);
    patchLocal(patch);
    schedule(patch);
  }

  async function ai<T>(label: string, fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(label);
    setErr("");
    setNeedsKey(false);
    try {
      return await fn();
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

  const doRewrite = () => {
    const range = selection();
    if (!range) {
      setErr("Select some text in the chapter first, then choose Rewrite.");
      return;
    }
    return ai("rewrite", async () => {
      const text = await runAi({ action: "rewrite", text: chapter.content.slice(...range), preset, context: aiContext });
      setResult({ kind: "rewrite", text, range });
    });
  };

  const doBrainstorm = () =>
    ai("brainstorm", async () => {
      const text = await runAi({ action: "brainstorm", text: chapter.content, instruction: direction, context: aiContext });
      setResult({ kind: "brainstorm", text });
    });

  const doSummarize = () =>
    ai("summarize", async () => {
      const text = await runAi({ action: "summarize", text: chapter.content });
      set("summary", text);
    });

  const doExtract = () =>
    ai("extract", async () => {
      const raw = await runAi({ action: "extract", text: chapter.content });
      const json = raw.slice(raw.indexOf("["), raw.lastIndexOf("]") + 1);
      let items: { name: string; category: EntityCategory; description: string }[] = [];
      try {
        items = JSON.parse(json);
      } catch {
        throw new AiClientError("The AI returned something unreadable. Try again.");
      }
      const known = new Set(entities.map((e) => e.name.toLowerCase()));
      const cats = ["Character", "Location", "Item", "Faction", "Lore"];
      setSuggestions(items.filter((i) => i?.name && cats.includes(i.category) && !known.has(i.name.toLowerCase())));
      if (!items.length) setErr("No new canon found in this chapter.");
    });

  async function addSuggestion(s: { name: string; category: EntityCategory; description: string }) {
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

  function applyResult(mode: "append" | "replace" | "insert") {
    if (!result) return;
    let next = chapter.content;
    if (mode === "replace" && result.range) next = next.slice(0, result.range[0]) + result.text + next.slice(result.range[1]);
    else if (mode === "insert" && result.range) next = next.slice(0, result.range[1]) + "\n\n" + result.text + next.slice(result.range[1]);
    else next = next.replace(/\s*$/, "") + (next.trim() ? "\n\n" : "") + result.text;
    set("content", next);
    setResult(null);
  }

  return (
    <>
      <section className="flex min-w-0 flex-col p-4 lg:p-8">
        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
          <div className="flex items-center justify-between gap-3">
            <input
              className="min-w-0 flex-1 bg-transparent font-serif text-2xl font-semibold outline-none"
              value={chapter.title}
              onChange={(e) => set("title", e.target.value)}
              aria-label="Chapter title"
            />
            <SaveBadge state={state} />
            <button onClick={() => setFocus(!focus)} className="cursor-pointer text-xs text-muted hover:text-text" title="Hide panels for distraction-free writing">
              {focus ? "Exit focus" : "Focus"}
            </button>
          </div>
          <textarea
            ref={textRef}
            className="mt-4 min-h-[60vh] flex-1 resize-none bg-transparent font-serif text-[17px] leading-8 outline-none placeholder:text-muted/50"
            value={chapter.content}
            onChange={(e) => set("content", e.target.value)}
            placeholder="Start writing…"
          />
          <p className="mt-2 text-xs text-muted">{chapter.word_count.toLocaleString()} words</p>
        </div>
      </section>

      <aside className={`space-y-4 border-t border-line p-4 lg:border-t-0 lg:border-l ${focus ? "hidden" : ""}`}>
        <div className="card p-4">
          <p className="text-sm font-semibold">✨ AI assistant</p>
          <textarea
            rows={2}
            className="input mt-3"
            placeholder="Optional direction, e.g. 'She discovers the key is fake'"
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
          />
          <div className="mt-2 flex items-center gap-2">
            <button onClick={doContinue} disabled={!!busy} className="btn-primary flex-1">
              {busy === "continue" ? "Writing…" : "Continue writing"}
            </button>
            <select className="input w-24 py-2" value={words} onChange={(e) => setWords(Number(e.target.value))} aria-label="Length">
              {[200, 400, 800, 1200].map((n) => (
                <option key={n} value={n}>
                  {n}w
                </option>
              ))}
            </select>
          </div>
          <button onClick={doBrainstorm} disabled={!!busy} className="btn-ghost mt-2 w-full">
            {busy === "brainstorm" ? "Thinking…" : "Brainstorm what's next"}
          </button>
          <div className="mt-4 border-t border-line pt-4">
            <p className="label">Rewrite selected text</p>
            <div className="flex gap-2">
              <select className="input py-2" value={preset} onChange={(e) => setPreset(e.target.value)}>
                {PRESETS.map((p) => (
                  <option key={p}>{p}</option>
                ))}
              </select>
              <button onClick={doRewrite} disabled={!!busy} className="btn-ghost">
                {busy === "rewrite" ? "…" : "Go"}
              </button>
            </div>
          </div>
          {err && (
            <p className="mt-3 text-sm text-danger">
              {err}{" "}
              {needsKey && (
                <a href="/app/settings" className="underline">
                  Open Settings
                </a>
              )}
            </p>
          )}
        </div>

        {result && (
          <div className="card border-accent/50 p-4">
            <p className="label">AI suggestion</p>
            <div className="max-h-72 overflow-y-auto font-serif text-sm leading-relaxed whitespace-pre-wrap">{result.text}</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {result.kind === "rewrite" ? (
                <>
                  <button onClick={() => applyResult("replace")} className="btn-primary">
                    Replace selection
                  </button>
                  <button onClick={() => applyResult("insert")} className="btn-ghost">
                    Insert after
                  </button>
                </>
              ) : result.kind === "continue" ? (
                <button onClick={() => applyResult("append")} className="btn-primary">
                  Add to chapter
                </button>
              ) : null}
              <button onClick={() => navigator.clipboard.writeText(result.text)} className="btn-ghost">
                Copy
              </button>
              <button onClick={() => setResult(null)} className="btn-ghost">
                Discard
              </button>
            </div>
          </div>
        )}

        <div className="card p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold">Chapter summary</p>
            <button onClick={doSummarize} disabled={!!busy || !chapter.content.trim()} className="cursor-pointer text-xs text-accent hover:underline disabled:opacity-40">
              {busy === "summarize" ? "Summarizing…" : "✨ Summarize"}
            </button>
          </div>
          <p className="mt-1 text-xs text-muted">Used as &quot;story so far&quot; context for later chapters.</p>
          <textarea rows={4} className="input mt-2" value={chapter.summary} onChange={(e) => set("summary", e.target.value)} />
        </div>

        <div className="card p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold">Canon scan</p>
            <button onClick={doExtract} disabled={!!busy || !chapter.content.trim()} className="cursor-pointer text-xs text-accent hover:underline disabled:opacity-40">
              {busy === "extract" ? "Scanning…" : "✨ Scan chapter"}
            </button>
          </div>
          <p className="mt-1 text-xs text-muted">Find new characters, places and lore to add to the World Bible.</p>
          {suggestions.length > 0 && (
            <ul className="mt-3 space-y-2">
              {suggestions.map((s) => (
                <li key={s.name} className="rounded-lg bg-panel-2 p-2 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">
                      {s.name} <span className="text-xs text-muted">· {s.category}</span>
                    </span>
                    <button onClick={() => addSuggestion(s)} className="cursor-pointer text-xs text-accent hover:underline">
                      Add
                    </button>
                  </div>
                  <p className="mt-1 text-xs text-muted">{s.description}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </>
  );
}
