"use client";
import { BookMarked, Building2, Gem, Loader2, MapPin, Plus, ScanSearch, ScrollText, Search, Sparkles, Trash2, UserRound, X, type LucideIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import EmptyState from "@/components/ui/EmptyState";
import { createClient } from "@/lib/supabase/client";
import { AiClientError, runAi } from "./aiClient";
import { ENTITY_CATEGORIES, type Chapter, type Entity, type EntityCategory, type Project } from "@/lib/types";
import { mentionedIn } from "@/lib/world-context";
import { scanChapters } from "./canonScan";

export const CATEGORY_ICONS: Record<EntityCategory, LucideIcon> = {
  Character: UserRound,
  Location: MapPin,
  Item: Gem,
  Faction: Building2,
  Lore: ScrollText,
};

type SortMode = "name" | "mentions" | "newest";

export default function WorldBibleTab({
  project,
  setProject,
  chapters,
  setChapters,
  entities,
  setEntities,
}: {
  project: Project;
  setProject: React.Dispatch<React.SetStateAction<Project>>;
  chapters: Chapter[];
  setChapters: React.Dispatch<React.SetStateAction<Chapter[]>>;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
}) {
  const supabase = createClient();
  const confirm = useConfirm();
  const [filter, setFilter] = useState<EntityCategory | "All">("All");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<Entity | null>(null);
  const [draft, setDraft] = useState({ name: "", category: "Character" as EntityCategory, description: "", aliases: "" });
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);
  const [expanding, setExpanding] = useState(false);
  const [sort, setSort] = useState<SortMode>("name");
  const [unusedOnly, setUnusedOnly] = useState(false);
  const [scanAll, setScanAll] = useState<{ done: number; total: number } | null>(null);
  const [scanMsg, setScanMsg] = useState("");

  // Which chapters mention each entry (original MANTIS "source markers" and "orphaned" filter).
  const ordered = useMemo(() => [...chapters].sort((a, b) => a.position - b.position), [chapters]);
  const appearsIn = useMemo(() => {
    const map = new Map<string, Chapter[]>();
    for (const c of ordered) for (const e of mentionedIn(entities, c.content)) map.set(e.id, [...(map.get(e.id) ?? []), c]);
    return map;
  }, [ordered, entities]);

  /** Read every chapter and update the World Bible and canon rules (original "Scan All Chapters"). */
  async function scanAllChapters() {
    if (!ordered.some((c) => c.content.trim().split(/\s+/).length >= 50)) return setScanMsg("Write a little in a chapter first, then scan.");
    setScanMsg("");
    setScanAll({ done: 0, total: ordered.length });
    try {
      const totals = await scanChapters(
        supabase,
        project,
        ordered,
        entities,
        (text, context) => runAi({ action: "extract", text, context }),
        ({ done, total, entities: known, canon, summaries }) => {
          setScanAll({ done, total });
          setEntities(known);
          setProject((prev) => ({ ...prev, canon_rules: canon }));
          setChapters((prev) => prev.map((c) => (summaries[c.id] ? { ...c, summary: summaries[c.id] } : c)));
        },
      );
      setScanMsg(
        totals.added + totals.updated + totals.facts
          ? `Done: ${totals.added} new ${totals.added === 1 ? "entry" : "entries"}, ${totals.updated} updated, ${totals.facts} canon ${totals.facts === 1 ? "rule" : "rules"} added.`
          : "Done. Everything was already up to date.",
      );
    } catch (e) {
      setScanMsg(e instanceof AiClientError ? e.message : "The scan stopped partway. What was found so far has been saved.");
    }
    setScanAll(null);
  }

  /** Expand the open entry's notes with AI (original MANTIS "enrich entity"). Appends; never deletes. */
  async function expand() {
    if (!draft.name.trim()) return setErr("Give this entry a name first.");
    setExpanding(true);
    setErr("");
    try {
      const text = await runAi({
        action: "enrich",
        text: draft.description,
        instruction: `${draft.name.trim()} (${draft.category})`,
        context: {
          project: {
            title: project.title,
            genre: project.genre,
            premise: project.premise,
            canon_rules: project.canon_rules,
            style_guide: project.style_guide,
          },
          entities: entities.filter((e) => e.id !== editing?.id).map((e) => ({ name: e.name, category: e.category, description: e.description })),
        },
      });
      setDraft((d) => ({ ...d, description: d.description.trim() ? `${d.description.trim()}\n${text.trim()}` : text.trim() }));
    } catch (e) {
      setErr(e instanceof AiClientError ? e.message : "AI request failed.");
    }
    setExpanding(false);
  }

  const shown = useMemo(() => {
    const q = query.toLowerCase();
    return entities
      .filter((e) => filter === "All" || e.category === filter)
      .filter(
        (e) =>
          !q ||
          e.name.toLowerCase().includes(q) ||
          e.description.toLowerCase().includes(q) ||
          e.aliases.some((a) => a.toLowerCase().includes(q)),
      )
      .filter((e) => !unusedOnly || !appearsIn.has(e.id))
      .sort((a, b) =>
        sort === "mentions"
          ? (appearsIn.get(b.id)?.length ?? 0) - (appearsIn.get(a.id)?.length ?? 0) || a.name.localeCompare(b.name)
          : sort === "newest"
            ? b.created_at.localeCompare(a.created_at)
            : a.name.localeCompare(b.name),
      );
  }, [entities, filter, query, unusedOnly, sort, appearsIn]);

  function startNew() {
    const category = filter === "All" ? "Character" : filter;
    setEditing({ id: "", project_id: project.id, name: "", category, description: "", aliases: [], created_at: "" });
    setDraft({ name: "", category, description: "", aliases: "" });
    setErr("");
  }

  function startEdit(e: Entity) {
    setEditing(e);
    setDraft({ name: e.name, category: e.category, description: e.description, aliases: e.aliases.join(", ") });
    setErr("");
  }

  async function save() {
    if (!draft.name.trim()) return setErr("Give this entry a name.");
    setSaving(true);
    const row = {
      name: draft.name.trim(),
      category: draft.category,
      description: draft.description,
      aliases: draft.aliases
        .split(",")
        .map((a) => a.trim())
        .filter(Boolean),
    };
    if (editing?.id) {
      const { error } = await supabase.from("entities").update(row).eq("id", editing.id);
      setSaving(false);
      if (error) return setErr(error.message);
      setEntities((prev) => prev.map((e) => (e.id === editing.id ? { ...e, ...row } : e)));
    } else {
      const { data, error } = await supabase
        .from("entities")
        .insert({ ...row, project_id: project.id, user_id: project.user_id })
        .select("*")
        .single();
      setSaving(false);
      if (error) return setErr(error.message);
      setEntities((prev) => [...prev, data as Entity]);
    }
    setEditing(null);
  }

  async function remove(e: Entity) {
    const ok = await confirm({ title: `Delete “${e.name}”?`, body: "It will be removed from the World Bible and the AI’s context.", confirmLabel: "Delete", danger: true });
    if (!ok) return;
    await supabase.from("entities").delete().eq("id", e.id);
    setEntities((prev) => prev.filter((x) => x.id !== e.id));
    if (editing?.id === e.id) setEditing(null);
  }

  const counts = Object.fromEntries(ENTITY_CATEGORIES.map((c) => [c, entities.filter((e) => e.category === c).length]));

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-semibold">World Bible</h1>
          <p className="mt-1 text-sm text-muted">The AI reads these entries before it writes, so your world stays consistent.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={scanAllChapters} disabled={!!scanAll} className="btn-ghost" title="Read every chapter and add what's missing">
            {scanAll ? <Loader2 size={16} className="animate-spin" /> : <ScanSearch size={16} />}
            {scanAll ? `Scanning ${scanAll.done + 1} of ${scanAll.total}…` : "Scan all chapters"}
          </button>
          <button onClick={startNew} className="btn-primary">
            <Plus size={16} /> New entry
          </button>
        </div>
      </div>
      {scanMsg && <p className="mt-3 rounded-lg border border-line bg-panel px-3 py-2 text-sm text-muted" role="status">{scanMsg}</p>}

      <div className="mt-6 flex flex-wrap items-center gap-2">
        {(["All", ...ENTITY_CATEGORIES] as const).map((c) => {
          const Icon = c === "All" ? BookMarked : CATEGORY_ICONS[c];
          const active = filter === c;
          return (
            <button
              key={c}
              onClick={() => setFilter(c)}
              className={`flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition ${
                active ? "border-accent bg-accent-soft text-accent" : "border-line text-muted hover:text-text"
              }`}
            >
              <Icon size={14} /> {c}
              <span className="text-xs opacity-70">{c === "All" ? entities.length : counts[c]}</span>
            </button>
          );
        })}
        <button
          onClick={() => setUnusedOnly((v) => !v)}
          className={`flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition ${
            unusedOnly ? "border-accent bg-accent-soft text-accent" : "border-line text-muted hover:text-text"
          }`}
          title="Entries no chapter mentions yet"
        >
          Not in any chapter
        </button>
        <select className="input w-auto py-1.5 text-sm" value={sort} onChange={(e) => setSort(e.target.value as SortMode)} aria-label="Sort entries">
          <option value="name">A to Z</option>
          <option value="mentions">Most mentioned</option>
          <option value="newest">Newest first</option>
        </select>
        <label className="relative ml-auto w-full sm:w-64">
          <Search size={15} className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted" />
          <input className="input pl-9" placeholder="Search names, aliases, notes" value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
      </div>

      <div className={`mt-6 grid gap-6 ${editing ? "lg:grid-cols-[minmax(0,1fr)_380px]" : ""}`}>
        <div>
          {entities.length === 0 ? (
            <EmptyState
              icon={BookMarked}
              title="Build your story world"
              body="MANTIS fills this in by itself as you write. You can also scan the chapters you already have, or add entries yourself."
              action={
                <div className="flex flex-wrap justify-center gap-2">
                  <button onClick={scanAllChapters} disabled={!!scanAll} className="btn-primary">
                    {scanAll ? <Loader2 size={16} className="animate-spin" /> : <ScanSearch size={16} />} Scan my chapters
                  </button>
                  <button onClick={startNew} className="btn-ghost">
                    <Plus size={16} /> Add an entry
                  </button>
                </div>
              }
            />
          ) : shown.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted">Nothing matches that search.</p>
          ) : (
            <div className={`grid gap-3 sm:grid-cols-2 ${editing ? "" : "xl:grid-cols-3"}`}>
              {shown.map((e) => {
                const Icon = CATEGORY_ICONS[e.category];
                return (
                  <button
                    key={e.id}
                    onClick={() => startEdit(e)}
                    className={`card cursor-pointer p-4 text-left transition hover:border-line-strong ${editing?.id === e.id ? "border-accent/60" : ""}`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-accent">
                        <Icon size={16} />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-medium">{e.name}</p>
                        <p className="text-xs text-muted">
                          {e.category}
                          {e.aliases.length > 0 && ` · aka ${e.aliases.join(", ")}`}
                        </p>
                      </div>
                    </div>
                    <p className="mt-3 line-clamp-3 text-sm whitespace-pre-line text-muted">{e.description || "No notes yet."}</p>
                    <p className="mt-2 text-[11px] text-muted/80">
                      {appearsIn.get(e.id)?.length
                        ? `In ${appearsIn.get(e.id)!.length} ${appearsIn.get(e.id)!.length === 1 ? "chapter" : "chapters"}`
                        : "Not in any chapter yet"}
                    </p>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {editing && (
          <div className="card h-fit p-5 lg:sticky lg:top-[120px]">
            <div className="flex items-center justify-between">
              <p className="font-semibold">{editing.id ? "Edit entry" : "New entry"}</p>
              <button onClick={() => setEditing(null)} className="btn-quiet h-8 w-8 p-0" aria-label="Close editor">
                <X size={16} />
              </button>
            </div>
            <div className="mt-4 space-y-4">
              <div>
                <label className="label" htmlFor="wb-name">
                  Name
                </label>
                <input id="wb-name" className="input" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} autoFocus />
              </div>
              <div>
                <span className="label">Category</span>
                <div className="flex flex-wrap gap-1.5">
                  {ENTITY_CATEGORIES.map((c) => {
                    const Icon = CATEGORY_ICONS[c];
                    return (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setDraft({ ...draft, category: c })}
                        className={`flex cursor-pointer items-center gap-1 rounded-full border px-2.5 py-1 text-xs transition ${
                          draft.category === c ? "border-accent bg-accent-soft text-accent" : "border-line text-muted hover:text-text"
                        }`}
                      >
                        <Icon size={12} /> {c}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <label className="label" htmlFor="wb-aliases">
                  Also known as <span className="normal-case">(comma separated)</span>
                </label>
                <input id="wb-aliases" className="input" value={draft.aliases} onChange={(e) => setDraft({ ...draft, aliases: e.target.value })} />
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <label className="label" htmlFor="wb-desc">
                    Notes
                  </label>
                  <button
                    type="button"
                    onClick={expand}
                    disabled={expanding}
                    className="mb-1.5 flex cursor-pointer items-center gap-1 text-xs text-accent hover:underline disabled:opacity-50"
                  >
                    {expanding ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                    {expanding ? "Expanding\u2026" : "Expand with AI"}
                  </button>
                </div>
                <textarea
                  id="wb-desc"
                  rows={9}
                  className="input leading-relaxed"
                  placeholder="Appearance, history, relationships, secrets…"
                  value={draft.description}
                  onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                />
              </div>
              {editing.id && (
                <p className="text-xs text-muted">
                  <span className="font-medium text-text/80">Appears in: </span>
                  {appearsIn.get(editing.id)?.map((c) => c.title || "Untitled").join(", ") || "no chapters yet"}
                </p>
              )}
              {err && <p className="rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{err}</p>}
              <div className="flex gap-2">
                <button onClick={save} disabled={saving} className="btn-primary flex-1">
                  {saving ? "Saving…" : "Save entry"}
                </button>
                {editing.id && (
                  <button onClick={() => remove(editing)} className="btn-danger" aria-label="Delete entry">
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
