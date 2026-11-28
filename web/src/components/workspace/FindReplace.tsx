"use client";
import { Replace, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { countWords, type Chapter, type Entity } from "@/lib/types";

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/**
 * Find and replace across the book (the original MANTIS had it per chapter). Every chapter it
 * changes gets a "Before find & replace" copy in History first, so nothing is lost.
 */
export default function FindReplace({
  chapters,
  activeId,
  userId,
  setChapters,
  entities,
  setEntities,
  onClose,
}: {
  chapters: Chapter[];
  activeId: string | null;
  userId: string;
  setChapters: React.Dispatch<React.SetStateAction<Chapter[]>>;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
  onClose: () => void;
}) {
  const supabase = createClient();
  const [find, setFind] = useState("");
  const [replace, setReplace] = useState("");
  const [matchCase, setMatchCase] = useState(false);
  const [wholeWord, setWholeWord] = useState(true);
  const [scope, setScope] = useState<"chapter" | "book">("book");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState("");
  const [inWorld, setInWorld] = useState(true);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const pattern = useMemo(() => {
    if (!find) return null;
    const body = escapeRe(find);
    return new RegExp(wholeWord ? `(?<![\\p{L}\\p{N}])${body}(?![\\p{L}\\p{N}])` : body, `gu${matchCase ? "" : "i"}`);
  }, [find, matchCase, wholeWord]);

  const ordered = [...chapters].sort((a, b) => a.position - b.position);
  const inScope = scope === "book" ? ordered : ordered.filter((c) => c.id === activeId);
  const hits = pattern
    ? inScope.map((c) => ({ c, count: (c.content.match(pattern) ?? []).length + (c.title.match(pattern) ?? []).length })).filter((h) => h.count > 0)
    : [];
  const total = hits.reduce((a, h) => a + h.count, 0);
  // World Bible entries that mention the term too (renaming a character should rename their entry).
  const test = (s: string) => !!pattern && new RegExp(pattern.source, pattern.flags.replace("g", "")).test(s);
  const worldHits = pattern ? entities.filter((e) => test(e.name) || e.aliases.some(test) || test(e.description)) : [];

  async function apply() {
    if (!pattern || (!hits.length && !(inWorld && worldHits.length))) return;
    setBusy(true);
    const updated: Chapter[] = [];
    for (const { c } of hits) {
      if (c.content.trim()) {
        await supabase.from("chapter_versions").insert({
          chapter_id: c.id,
          project_id: c.project_id,
          user_id: userId,
          title: c.title,
          content: c.content,
          word_count: c.word_count,
          reason: "Before find & replace",
        });
      }
      const content = c.content.replace(pattern, () => replace);
      const title = c.title.replace(pattern, () => replace);
      const word_count = countWords(content);
      const updated_at = new Date().toISOString();
      const { error } = await supabase.from("chapters").update({ content, title, word_count, updated_at }).eq("id", c.id);
      if (!error) updated.push({ ...c, content, title, word_count, updated_at });
    }
    setChapters((prev) => prev.map((c) => updated.find((u) => u.id === c.id) ?? c));
    const renamed: Entity[] = [];
    if (inWorld) {
      for (const e of worldHits) {
        const next = {
          name: e.name.replace(pattern, () => replace).trim() || e.name,
          aliases: e.aliases.map((a) => a.replace(pattern, () => replace).trim()).filter(Boolean),
          description: e.description.replace(pattern, () => replace),
        };
        const { error } = await supabase.from("entities").update(next).eq("id", e.id);
        if (!error) renamed.push({ ...e, ...next });
      }
      setEntities((prev) => prev.map((e) => renamed.find((r) => r.id === e.id) ?? e));
    }
    setBusy(false);
    const world = renamed.length ? `${renamed.length} World Bible ${renamed.length === 1 ? "entry" : "entries"}` : "";
    setDone(
      updated.length
        ? `Replaced ${total} ${total === 1 ? "match" : "matches"} in ${updated.length} ${updated.length === 1 ? "chapter" : "chapters"}${world ? ` and updated ${world}` : ""}. Changed chapters have a copy in History.`
        : `Updated ${world || "nothing"}.`,
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 p-4 pt-[12vh]" onClick={onClose}>
      <div role="dialog" aria-label="Find and replace" className="card w-full max-w-md p-5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <p className="flex items-center gap-2 font-semibold">
            <Replace size={16} className="text-accent" /> Find and replace
          </p>
          <button onClick={onClose} className="btn-quiet h-8 w-8 p-0" aria-label="Close">
            <X size={16} />
          </button>
        </div>
        <div className="mt-4 space-y-3">
          <div>
            <label className="label" htmlFor="fr-find">
              Find
            </label>
            <input id="fr-find" className="input" value={find} onChange={(e) => (setFind(e.target.value), setDone(""))} autoFocus placeholder="e.g. Mara" />
          </div>
          <div>
            <label className="label" htmlFor="fr-replace">
              Replace with
            </label>
            <input id="fr-replace" className="input" value={replace} onChange={(e) => (setReplace(e.target.value), setDone(""))} placeholder="e.g. Maren" />
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted">
            <label className="flex cursor-pointer items-center gap-1.5">
              <input type="checkbox" checked={wholeWord} onChange={(e) => setWholeWord(e.target.checked)} /> Whole words
            </label>
            <label className="flex cursor-pointer items-center gap-1.5">
              <input type="checkbox" checked={matchCase} onChange={(e) => setMatchCase(e.target.checked)} /> Match case
            </label>
            <label className="flex cursor-pointer items-center gap-1.5">
              <input type="radio" name="fr-scope" checked={scope === "book"} onChange={() => setScope("book")} /> Whole book
            </label>
            <label className="flex cursor-pointer items-center gap-1.5">
              <input type="radio" name="fr-scope" checked={scope === "chapter"} onChange={() => setScope("chapter")} /> This chapter
            </label>
          </div>
          {worldHits.length > 0 && !done && (
            <label className="flex cursor-pointer items-start gap-1.5 text-sm text-muted">
              <input type="checkbox" className="mt-1" checked={inWorld} onChange={(e) => setInWorld(e.target.checked)} />
              <span>
                Also update {worldHits.length === 1 ? "the World Bible entry" : `${worldHits.length} World Bible entries`}: {worldHits.slice(0, 3).map((e) => e.name).join(", ")}
                {worldHits.length > 3 ? "…" : ""}
              </span>
            </label>
          )}
          {find && !done && (
            <p className="text-sm text-muted" aria-live="polite">
              {total ? `${total} ${total === 1 ? "match" : "matches"} in ${hits.map((h) => h.c.title || "Untitled").slice(0, 5).join(", ")}${hits.length > 5 ? ` and ${hits.length - 5} more` : ""}.` : worldHits.length ? "Not in any chapter." : "No matches."}
            </p>
          )}
          {done && <p className="rounded-lg border border-accent/30 bg-accent-soft px-3 py-2 text-sm text-accent">{done}</p>}
          <div className="flex justify-end gap-2">
            <button onClick={onClose} className="btn-ghost">
              {done ? "Close" : "Cancel"}
            </button>
            <button onClick={apply} disabled={(!total && !(inWorld && worldHits.length)) || busy} className="btn-primary">
              {busy ? "Replacing…" : `Replace ${total || ""}`.trim()}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
