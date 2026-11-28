"use client";
import { Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { LINK_KINDS, type Chapter, type Entity, type EntityLink, type LinkKind } from "@/lib/types";
import { mentions, nameForms } from "@/lib/world-context";

const SIZE = 560;
const C = SIZE / 2;

/**
 * Relationship map (original MANTIS "Relationship graph"): who shares chapters with whom,
 * plus the links the writer draws (ally, rival, family…), which the AI also reads.
 */
export default function RelationshipMap({
  project,
  chapters,
  entities,
  links,
  setLinks,
}: {
  project: { id: string; user_id: string };
  chapters: Chapter[];
  entities: Entity[];
  links: EntityLink[];
  setLinks: React.Dispatch<React.SetStateAction<EntityLink[]>>;
}) {
  const supabase = createClient();
  const [selected, setSelected] = useState<string | null>(null);
  const [target, setTarget] = useState("");
  const [kind, setKind] = useState<LinkKind>("ally");
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");

  // Which chapters each entry appears in, then shared-chapter weights for every pair.
  const { nodes, shared } = useMemo(() => {
    const seen = new Map<string, Set<string>>();
    for (const e of entities) {
      const forms = nameForms(e);
      seen.set(e.id, new Set(chapters.filter((c) => c.content && mentions(c.content, forms)).map((c) => c.id)));
    }
    const linked = new Set(links.flatMap((l) => [l.source_id, l.target_id]));
    const nodes = entities
      .filter((e) => (e.category === "Character" || e.category === "Faction" || linked.has(e.id)) && ((seen.get(e.id)?.size ?? 0) > 0 || linked.has(e.id)))
      .sort((a, b) => (seen.get(b.id)?.size ?? 0) - (seen.get(a.id)?.size ?? 0))
      .slice(0, 20);
    const shared: { a: string; b: string; n: number }[] = [];
    for (let i = 0; i < nodes.length; i++)
      for (let j = i + 1; j < nodes.length; j++) {
        const A = seen.get(nodes[i].id)!;
        const n = [...(seen.get(nodes[j].id) ?? [])].filter((x) => A.has(x)).length;
        if (n) shared.push({ a: nodes[i].id, b: nodes[j].id, n });
      }
    return { nodes: nodes.map((e) => ({ e, count: seen.get(e.id)?.size ?? 0 })), shared };
  }, [entities, chapters, links]);

  const pos = useMemo(() => {
    const m = new Map<string, { x: number; y: number }>();
    const r = SIZE / 2 - 70;
    nodes.forEach(({ e }, i) => {
      const t = (i / Math.max(1, nodes.length)) * Math.PI * 2 - Math.PI / 2;
      m.set(e.id, { x: C + r * Math.cos(t), y: C + r * Math.sin(t) });
    });
    return m;
  }, [nodes]);

  const maxShared = Math.max(1, ...shared.map((s) => s.n));
  const touches = (a: string, b: string) => !selected || a === selected || b === selected;
  const sel = entities.find((e) => e.id === selected) ?? null;
  const name = (id: string) => entities.find((e) => e.id === id)?.name ?? "?";

  async function addLink() {
    if (!selected || !target) return;
    setErr("");
    const { data, error } = await supabase
      .from("entity_links")
      .upsert({ project_id: project.id, user_id: project.user_id, source_id: selected, target_id: target, kind, note: note.trim() }, { onConflict: "source_id,target_id" })
      .select("id, project_id, source_id, target_id, kind, note")
      .single();
    if (error || !data) return setErr(error?.message ?? "Couldn't save that link.");
    setLinks((prev) => [...prev.filter((l) => l.id !== data.id && !(l.source_id === selected && l.target_id === target)), data as EntityLink]);
    setNote("");
  }

  async function removeLink(id: string) {
    const { error } = await supabase.from("entity_links").delete().eq("id", id);
    if (!error) setLinks((prev) => prev.filter((l) => l.id !== id));
  }

  if (!nodes.length) {
    return <p className="py-10 text-center text-sm text-muted">Characters show up here once they appear in your chapters. Add some to the World Bible or scan your chapters.</p>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="card p-3">
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="mx-auto block w-full max-w-[560px]" role="img" aria-label="Relationship map of characters">
          {shared.map((s) => {
            const a = pos.get(s.a)!;
            const b = pos.get(s.b)!;
            return (
              <line key={`${s.a}-${s.b}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="var(--color-muted)" strokeOpacity={touches(s.a, s.b) ? 0.25 + (0.45 * s.n) / maxShared : 0.06} strokeWidth={1 + (3 * s.n) / maxShared}>
                <title>{`${name(s.a)} & ${name(s.b)}: ${s.n} shared ${s.n === 1 ? "chapter" : "chapters"}`}</title>
              </line>
            );
          })}
          {links.map((l) => {
            const a = pos.get(l.source_id);
            const b = pos.get(l.target_id);
            if (!a || !b) return null;
            const on = touches(l.source_id, l.target_id);
            return (
              <g key={l.id} opacity={on ? 1 : 0.15}>
                <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="var(--color-accent)" strokeWidth={2} strokeDasharray={l.kind === "enemy" || l.kind === "rival" ? "6 4" : undefined} />
                <text x={(a.x + b.x) / 2} y={(a.y + b.y) / 2 - 4} textAnchor="middle" fontSize="11" fill="var(--color-text)" stroke="var(--color-panel)" strokeWidth={3} paintOrder="stroke">
                  {l.kind}
                </text>
              </g>
            );
          })}
          {nodes.map(({ e, count }) => {
            const p = pos.get(e.id)!;
            const r = 6 + Math.min(10, count * 1.5);
            const active = selected === e.id;
            return (
              <g key={e.id} onClick={() => setSelected(active ? null : e.id)} className="cursor-pointer">
                <circle cx={p.x} cy={p.y} r={r + 8} fill="transparent" />
                <circle cx={p.x} cy={p.y} r={r} fill={active ? "var(--color-accent)" : "var(--color-panel-3)"} stroke="var(--color-accent)" strokeWidth={2} />
                <text x={p.x} y={p.y + r + 14} textAnchor="middle" fontSize="12" fill="var(--color-text)" stroke="var(--color-bg)" strokeWidth={3} paintOrder="stroke">
                  {e.name.length > 18 ? `${e.name.slice(0, 17)}…` : e.name}
                </text>
                <title>{`${e.name}: in ${count} ${count === 1 ? "chapter" : "chapters"}`}</title>
              </g>
            );
          })}
        </svg>
        <p className="mt-1 text-center text-[11px] text-muted">Grey lines: shared chapters (thicker = more). Green lines: links you added (dashed = rival or enemy). Click a name to focus.</p>
      </div>

      <aside className="card h-fit p-5">
        {!sel ? (
          <p className="text-sm text-muted">Click a character on the map to see and add their relationships. The AI reads every link you add.</p>
        ) : (
          <>
            <p className="font-semibold">{sel.name}</p>
            <ul className="mt-3 space-y-1.5 text-sm">
              {links
                .filter((l) => l.source_id === sel.id || l.target_id === sel.id)
                .map((l) => (
                  <li key={l.id} className="flex items-start justify-between gap-2 rounded-lg border border-line px-2 py-1.5">
                    <span>
                      <span className="text-accent">{l.kind}</span> of {name(l.source_id === sel.id ? l.target_id : l.source_id)}
                      {l.note && <span className="block text-xs text-muted">{l.note}</span>}
                    </span>
                    <button onClick={() => void removeLink(l.id)} className="btn-quiet h-6 w-6 shrink-0 p-0" aria-label="Remove link">
                      <Trash2 size={12} />
                    </button>
                  </li>
                ))}
              {shared
                .filter((s) => s.a === sel.id || s.b === sel.id)
                .sort((x, y) => y.n - x.n)
                .slice(0, 6)
                .map((s) => (
                  <li key={`${s.a}${s.b}`} className="px-2 text-xs text-muted">
                    Shares {s.n} {s.n === 1 ? "chapter" : "chapters"} with {name(s.a === sel.id ? s.b : s.a)}
                  </li>
                ))}
            </ul>
            <div className="mt-4 space-y-2 border-t border-line pt-4">
              <p className="text-xs font-medium">Add a relationship</p>
              <div className="flex gap-2">
                <select className="input py-1.5 text-sm" value={kind} onChange={(e) => setKind(e.target.value as LinkKind)} aria-label="Relationship">
                  {LINK_KINDS.map((k) => (
                    <option key={k}>{k}</option>
                  ))}
                </select>
                <select className="input py-1.5 text-sm" value={target} onChange={(e) => setTarget(e.target.value)} aria-label="With">
                  <option value="">of…</option>
                  {entities
                    .filter((e) => e.id !== sel.id)
                    .map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.name}
                      </option>
                    ))}
                </select>
              </div>
              <input className="input py-1.5 text-sm" placeholder="Note (optional), e.g. “older sister, estranged”" value={note} onChange={(e) => setNote(e.target.value)} />
              {err && <p className="text-xs text-danger">{err}</p>}
              <button onClick={() => void addLink()} disabled={!target} className="btn-primary w-full py-1.5">
                <Plus size={14} /> Add
              </button>
            </div>
          </>
        )}
      </aside>
    </div>
  );
}
