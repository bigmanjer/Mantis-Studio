"use client";
import { BookMarked, Building2, Gem, Loader2, MapPin, Plus, ScrollText, Search, Sparkles, Trash2, UserRound, X, type LucideIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import EmptyState from "@/components/ui/EmptyState";
import { createClient } from "@/lib/supabase/client";
import { AiClientError, runAi } from "./aiClient";
import { ENTITY_CATEGORIES, type Entity, type EntityCategory, type Project } from "@/lib/types";

export const CATEGORY_ICONS: Record<EntityCategory, LucideIcon> = {
  Character: UserRound,
  Location: MapPin,
  Item: Gem,
  Faction: Building2,
  Lore: ScrollText,
};

export default function WorldBibleTab({
  project,
  entities,
  setEntities,
}: {
  project: Project;
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
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [entities, filter, query]);

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
        <button onClick={startNew} className="btn-primary">
          <Plus size={16} /> New entry
        </button>
      </div>

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
              body="Add characters, places and lore yourself, or use Canon scan in the Write tab to pull them straight from your chapters."
              action={
                <button onClick={startNew} className="btn-primary">
                  <Plus size={16} /> Add the first entry
                </button>
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
