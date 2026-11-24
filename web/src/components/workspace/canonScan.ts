"use client";
import type { SupabaseClient } from "@supabase/supabase-js";
import { ENTITY_CATEGORIES, type Entity, type EntityCategory } from "@/lib/types";
import { nameForms, overlap } from "@/lib/world-context";

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
  // Look entries up by every form of their name ("the brass key" is also "brass key"; "Ivy Marsh" is also "Ivy").
  const byName = new Map<string, Entity>();
  const add = (form: string, e: Entity) => {
    const k = norm(form);
    if (k && !byName.has(k)) byName.set(k, e);
  };
  for (const e of entities) for (const f of nameForms(e)) add(f, e);

  const creates: ScannedEntity[] = [];
  const merges = new Map<string, { entity: Entity; newFacts: string[]; newAliases: string[] }>();
  const pending = new Map<string, ScannedEntity>();

  for (const item of scan.entities) {
    const forms = nameForms(item);
    const existing = forms.map((f) => byName.get(norm(f))).find(Boolean);
    if (!existing) {
      // Same new thing listed twice in one scan: fold it into the first.
      const twin = forms.map((f) => pending.get(norm(f))).find(Boolean);
      if (twin) {
        twin.aliases = [...new Set([...twin.aliases, item.name, ...item.aliases].filter((a) => norm(a) !== norm(twin.name)))];
        continue;
      }
      creates.push(item);
      for (const f of forms) if (!pending.has(norm(f))) pending.set(norm(f), item);
      continue;
    }
    // Keep only sentences that say something new, like the original MANTIS merge.
    const have = existing.description.split(/\n|(?<=[.!?])\s+/).map((s) => s.replace(/^[-•*]\s*/, "").trim()).filter(Boolean);
    const prev = merges.get(existing.id);
    const already = [...have, ...(prev?.newFacts ?? [])];
    const newFacts = item.description
      .split(/(?<=[.!?])\s+/)
      .map((f) => f.trim())
      .filter((f) => f.length > 3 && !already.some((h) => overlap(f, h) >= 0.6));
    const known = new Set(nameForms(existing).map(norm));
    const newAliases = [item.name, ...item.aliases].filter((a) => !known.has(norm(a)) && !known.has(norm(a.replace(/^(the|a|an)\s+/i, ""))));
    if (!newFacts.length && !newAliases.length) continue;
    if (prev) {
      prev.newFacts.push(...newFacts);
      prev.newAliases.push(...newAliases.filter((a) => !prev.newAliases.some((x) => norm(x) === norm(a))));
    } else {
      merges.set(existing.id, { entity: existing, newFacts, newAliases: [...new Map(newAliases.map((a) => [norm(a), a])).values()] });
    }
  }

  // Canon rules: skip anything the rules already say, even in other words. At most 3 per scan.
  const ruleLines = canonRules.split("\n").map((l) => l.trim()).filter(Boolean);
  const facts: string[] = [];
  for (const f of scan.facts) {
    if (facts.length >= 3) break;
    if ([...ruleLines, ...facts].some((r) => overlap(f, r) >= 0.6)) continue;
    facts.push(f);
  }
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

/**
 * Scan many chapters in a row, carrying what each one found into the next (original "Scan All
 * Chapters"). Fills empty chapter summaries too. Stops at the first AI error, keeping what was saved.
 */
export async function scanChapters(
  supabase: SupabaseClient,
  project: { id: string; user_id: string; canon_rules: string },
  chapters: { id: string; content: string; summary: string }[],
  entities: Entity[],
  runExtract: (text: string, context: unknown) => Promise<string>,
  onProgress: (state: { done: number; total: number; entities: Entity[]; canon: string; summaries: Record<string, string> }) => void,
) {
  const todo = chapters.filter((c) => c.content.trim().split(/\s+/).length >= 50);
  let known = entities;
  let canon = project.canon_rules ?? "";
  const summaries: Record<string, string> = {};
  const totals = { added: 0, updated: 0, facts: 0, chapters: todo.length };
  for (const [i, c] of todo.entries()) {
    const raw = await runExtract(c.content, {
      project: { canon_rules: canon },
      entities: known.map((e) => ({ name: e.name, category: e.category, description: "" })),
    });
    const plan = planScan(parseScan(raw), known, canon);
    if (plan.summary && !c.summary.trim()) {
      const { error } = await supabase.from("chapters").update({ summary: plan.summary }).eq("id", c.id);
      if (!error) summaries[c.id] = plan.summary;
    }
    if (!planIsEmpty(plan)) {
      const applied = await applyScan(supabase, plan, { id: project.id, user_id: project.user_id, canon_rules: canon }, { includeFacts: true });
      known = known.map((e) => {
        const m = plan.merges.find((x) => x.entity.id === e.id);
        return m && applied.updated.some((u) => u.id === e.id)
          ? { ...e, description: [e.description.trim(), ...m.newFacts.map((f) => `- ${f}`)].filter(Boolean).join("\n"), aliases: [...e.aliases, ...m.newAliases].slice(0, 30) }
          : e;
      });
      known = [...known, ...applied.created];
      if (applied.factsAdded.length) canon = [canon.trim(), ...applied.factsAdded].filter(Boolean).join("\n");
      totals.added += applied.created.length;
      totals.updated += applied.updated.length;
      totals.facts += applied.factsAdded.length;
    }
    onProgress({ done: i + 1, total: todo.length, entities: known, canon, summaries });
  }
  return totals;
}
