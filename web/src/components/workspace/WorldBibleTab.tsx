"use client";
import { useMemo, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { ENTITY_CATEGORIES, type Entity, type EntityCategory, type Project } from "@/lib/types";

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
  const [filter, setFilter] = useState<EntityCategory | "All">("All");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<Entity | null>(null);
  const [draft, setDraft] = useState({ name: "", category: "Character" as EntityCategory, description: "", aliases: "" });
  const [err, setErr] = useState("");

  const shown = useMemo(() => {
    const q = query.toLowerCase();
    return entities
      .filter((e) => filter === "All" || e.category === filter)
      .filter((e) => !q || e.name.toLowerCase().includes(q) || e.description.toLowerCase().includes(q) || e.aliases.some((a) => a.toLowerCase().includes(q)))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [entities, filter, query]);

  function startNew() {
    setEditing({ id: "", project_id: project.id, name: "", category: filter === "All" ? "Character" : filter, description: "", aliases: [], created_at: "" });
    setDraft({ name: "", category: filter === "All" ? "Character" : filter, description: "", aliases: "" });
    setErr("");
  }

  function startEdit(e: Entity) {
    setEditing(e);
    setDraft({ name: e.name, category: e.category, description: e.description, aliases: e.aliases.join(", ") });
    setErr("");
  }

  async function save() {
    if (!draft.name.trim()) {
      setErr("Name is required.");
      return;
    }
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
      if (error) return setErr(error.message);
      setEntities(entities.map((e) => (e.id === editing.id ? { ...e, ...row } : e)));
    } else {
      const { data, error } = await supabase
        .from("entities")
        .insert({ ...row, project_id: project.id, user_id: project.user_id })
        .select("*")
        .single();
      if (error) return setErr(error.message);
      setEntities([...entities, data as Entity]);
    }
    setEditing(null);
  }

  async function remove(e: Entity) {
    if (!window.confirm(`Delete "${e.name}" from the World Bible?`)) return;
    await supabase.from("entities").delete().eq("id", e.id);
    setEntities(entities.filter((x) => x.id !== e.id));
    if (editing?.id === e.id) setEditing(null);
  }

  const counts = Object.fromEntries(ENTITY_CATEGORIES.map((c) => [c, entities.filter((e) => e.category === c).length]));

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-wrap items-center gap-2">
        {(["All", ...ENTITY_CATEGORIES] as const).map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            className={`cursor-pointer rounded-full px-3 py-1 text-sm ${filter === c ? "bg-accent text-black" : "bg-panel-2 text-muted hover:text-text"}`}
          >
            {c} {c !== "All" && <span className="opacity-60">{counts[c]}</span>}
          </button>
        ))}
        <input className="input ml-auto w-full sm:w-56" placeholder="Search…" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button onClick={startNew} className="btn-primary">
          + New entry
        </button>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_380px]">
        <div className="grid content-start gap-3 sm:grid-cols-2">
          {shown.length === 0 && (
            <p className="text-sm text-muted sm:col-span-2">
              {entities.length ? "No matches." : "Nothing here yet. Add entries yourself, or use “Scan chapter” in the Write tab to pull canon from your draft."}
            </p>
          )}
          {shown.map((e) => (
            <button
              key={e.id}
              onClick={() => startEdit(e)}
              className={`card cursor-pointer p-4 text-left transition hover:border-accent/50 ${editing?.id === e.id ? "border-accent/60" : ""}`}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-medium">{e.name}</p>
                <span className="text-xs text-muted">{e.category}</span>
              </div>
              {e.aliases.length > 0 && <p className="mt-0.5 text-xs text-muted">aka {e.aliases.join(", ")}</p>}
              <p className="mt-2 line-clamp-3 text-sm whitespace-pre-line text-muted">{e.description || "No description yet."}</p>
            </button>
          ))}
        </div>

        {editing && (
          <div className="card h-fit space-y-3 p-5 lg:sticky lg:top-4">
            <p className="font-semibold">{editing.id ? "Edit entry" : "New entry"}</p>
            <div>
              <label className="label">Name</label>
              <input className="input" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} autoFocus />
            </div>
            <div>
              <label className="label">Category</label>
              <select className="input" value={draft.category} onChange={(e) => setDraft({ ...draft, category: e.target.value as EntityCategory })}>
                {ENTITY_CATEGORIES.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Aliases (comma separated)</label>
              <input className="input" value={draft.aliases} onChange={(e) => setDraft({ ...draft, aliases: e.target.value })} />
            </div>
            <div>
              <label className="label">Description</label>
              <textarea rows={8} className="input" value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })} />
            </div>
            {err && <p className="text-sm text-danger">{err}</p>}
            <div className="flex gap-2">
              <button onClick={save} className="btn-primary flex-1">
                Save
              </button>
              <button onClick={() => setEditing(null)} className="btn-ghost">
                Cancel
              </button>
              {editing.id && (
                <button onClick={() => remove(editing)} className="btn-danger">
                  Delete
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
