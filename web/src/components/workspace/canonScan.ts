"use client";
import type { SupabaseClient } from "@supabase/supabase-js";
import { ENTITY_CATEGORIES, type Entity, type EntityCategory } from "@/lib/types";

export interface ScannedEntity {
  name: string;
  category: EntityCategory;
  description: string;
  aliases: string[];
}

export interface ScanPlan {
  summary: string;
  /** Entries that don't exist yet. */
  creates: ScannedEntity[];
  /** Existing entries that gained new details or names. */
  merges: { entity: Entity; newFacts: string[]; newAliases: string[] }[];
  /** New firm facts for the canon rules. */
  facts: string[];
}

export interface AppliedScan {
  created: Entity[];
  updated: { id: string; description: string; aliases: string[] }[];
  canonBefore: string | null;
  factsAdded: string[];
  summary: string;
}

const norm = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N} ]/gu, "").replace(/\s+/g, " ").trim();

/** Read the AI's scan. Accepts the current object format and the older plain-array format. */
export function parseScan(raw: string): { summary: string; entities: ScannedEntity[]; facts: string[] } {
  const firstObj = raw.indexOf("{");
  const firstArr = raw.indexOf("[");
  let data: unknown;
  if (firstArr >= 0 && (firstObj < 0 || firstArr < firstObj)) {
    data = { entities: JSON.parse(raw.slice(firstArr, raw.lastIndexOf("]") + 1)) };
  } else {
    data = JSON.parse(raw.slice(firstObj, raw.lastIndexOf("}") + 1));
  }
  const d = (data ?? {}) as Record<string, unknown>;
  const list = Array.isArray(d.entities) ? (d.entities as Record<string, unknown>[]) : [];
  const entities = list
    .filter((e) => e && typeof e.name === "string" && e.name.trim() && ENTITY_CATEGORIES.includes(e.category as EntityCategory))
    .map((e) => ({
      name: String(e.name).trim().slice(0, 200),
      category: e.category as EntityCategory,
      description: typeof e.description === "string" ? e.description.trim() : "",
      aliases: Array.isArray(e.aliases) ? e.aliases.filter((a): a is string => typeof a === "string" && !!a.trim()).map((a) => a.trim().slice(0, 100)) : [],
    }));
  const facts = Array.isArray(d.facts) ? d.facts.filter((f): f is string => typeof f === "string" && f.trim().length > 3).map((f) => f.trim()) : [];
  return { summary: typeof d.summary === "string" ? d.summary.trim() : "", entities, facts };
}

/** Work out what the scan adds, merging into existing entries instead of creating duplicates. */
export function planScan(scan: ReturnType<typeof parseScan>, entities: Entity[], canonRules: string): ScanPlan {
  const byName = new Map<string, Entity>();
  for (const e of entities) {
    byName.set(norm(e.name), e);
    for (const a of e.aliases) byName.set(norm(a), e);
  }
  const creates: ScannedEntity[] = [];
  const merges = new Map<string, { entity: Entity; newFacts: string[]; newAliases: string[] }>();
  const seenNew = new Set<string>();

  for (const item of scan.entities) {
    const existing = byName.get(norm(item.name)) ?? item.aliases.map((a) => byName.get(norm(a))).find(Boolean);
    if (!existing) {
      if (seenNew.has(norm(item.name))) continue;
      seenNew.add(norm(item.name));
      creates.push(item);
      continue;
    }
    // Keep only sentences that say something new, like the original MANTIS merge.
    const have = norm(existing.description);
    const newFacts = item.description
      .split(/(?<=[.!?])\s+/)
      .map((f) => f.trim())
      .filter((f) => f.length > 3 && !have.includes(norm(f)));
    const known = new Set([norm(existing.name), ...existing.aliases.map(norm)]);
    const newAliases = [item.name, ...item.aliases].filter((a) => !known.has(norm(a)));
    if (!newFacts.length && !newAliases.length) continue;
    const prev = merges.get(existing.id);
    if (prev) {
      prev.newFacts.push(...newFacts.filter((f) => !prev.newFacts.includes(f)));
      prev.newAliases.push(...newAliases.filter((a) => !prev.newAliases.some((x) => norm(x) === norm(a))));
    } else {
      merges.set(existing.id, { entity: existing, newFacts, newAliases: [...new Map(newAliases.map((a) => [norm(a), a])).values()] });
    }
  }

  const rulesNorm = norm(canonRules);
  const facts = scan.facts.filter((f) => !rulesNorm.includes(norm(f))).slice(0, 5);
  return { summary: scan.summary, creates, merges: [...merges.values()], facts };
}

export const planIsEmpty = (p: ScanPlan) => !p.creates.length && !p.merges.length && !p.facts.length;

/** Save the whole plan. Returns what changed so it can be undone. */
export async function applyScan(
  supabase: SupabaseClient,
  plan: ScanPlan,
  project: { id: string; user_id: string; canon_rules: string },
  opts: { includeFacts: boolean },
): Promise<AppliedScan> {
  const applied: AppliedScan = { created: [], updated: [], canonBefore: null, factsAdded: [], summary: plan.summary };

  if (plan.creates.length) {
    const { data } = await supabase
      .from("entities")
      .insert(plan.creates.map((c) => ({ project_id: project.id, user_id: project.user_id, name: c.name, category: c.category, description: c.description, aliases: c.aliases })))
      .select("*");
    applied.created = (data ?? []) as Entity[];
  }

  for (const m of plan.merges) {
    const description = [m.entity.description.trim(), ...m.newFacts.map((f) => `- ${f}`)].filter(Boolean).join("\n");
    const aliases = [...m.entity.aliases, ...m.newAliases].slice(0, 30);
    const { error } = await supabase.from("entities").update({ description, aliases }).eq("id", m.entity.id);
    if (!error) applied.updated.push({ id: m.entity.id, description: m.entity.description, aliases: m.entity.aliases });
  }

  if (opts.includeFacts && plan.facts.length) {
    const before = project.canon_rules ?? "";
    const next = [before.trim(), ...plan.facts].filter(Boolean).join("\n");
    const { error } = await supabase.from("projects").update({ canon_rules: next }).eq("id", project.id);
    if (!error) {
      applied.canonBefore = before;
      applied.factsAdded = plan.facts;
    }
  }
  return applied;
}

/** Put everything back the way it was before an automatic scan. */
export async function undoScan(supabase: SupabaseClient, applied: AppliedScan, projectId: string) {
  if (applied.created.length) await supabase.from("entities").delete().in("id", applied.created.map((e) => e.id));
  for (const u of applied.updated) await supabase.from("entities").update({ description: u.description, aliases: u.aliases }).eq("id", u.id);
  if (applied.canonBefore !== null) await supabase.from("projects").update({ canon_rules: applied.canonBefore }).eq("id", projectId);
}
