import type { Chapter, Entity, Project } from "./types";
import { mentions, nameForms } from "./world-context";

/** Where a suggested fix lives in the workspace. */
export type InsightTarget = "plan" | "write" | "world" | "library";

export interface Risk {
  level: "high" | "medium" | "low";
  text: string;
  detail?: string;
  target: InsightTarget;
}

export interface Readiness {
  label: string;
  ok: boolean;
  hint: string;
  target: InsightTarget;
}

export interface Insights {
  totalWords: number;
  target: number;
  drafted: number;
  chapterCount: number;
  avgWords: number;
  /** Per chapter, in order: words and whether it's unusually long or short. */
  lengths: { id: string; title: string; words: number; flag: "long" | "short" | null }[];
  summaries: { have: number; need: number };
  outlineChapters: number;
  /** Entry id -> chapter ids that mention it (by name, alias, or short form). */
  appears: Map<string, string[]>;
  orphaned: Entity[];
  thin: Entity[];
  duplicates: [Entity, Entity][];
  /** Most present characters with the chapters they appear in, for the presence grid. */
  cast: { entity: Entity; chapters: Set<string> }[];
  /** Characters who appeared earlier but are missing from the last few chapters. */
  vanished: { entity: Entity; lastSeen: string }[];
  risks: Risk[];
  readiness: Readiness[];
  readinessScore: number;
  next: { text: string; why: string; target: InsightTarget; cta: string };
}

const norm = (s: string) => s.toLowerCase().replace(/^(the|a|an)\s+/, "").replace(/[^\p{L}\p{N} ]/gu, "").trim();

export function computeInsights(project: Project, chapters: Chapter[], entities: Entity[]): Insights {
  const ordered = [...chapters].sort((a, b) => a.position - b.position);
  const written = ordered.filter((c) => c.word_count > 0);
  const totalWords = ordered.reduce((a, c) => a + (c.word_count || 0), 0);
  const avgWords = written.length ? Math.round(totalWords / written.length) : 0;
  const target = project.target_words || 80000;

  const lengths = ordered.map((c) => ({
    id: c.id,
    title: c.title || "Untitled",
    words: c.word_count,
    flag: (written.length >= 3 && c.word_count > 0 ? (c.word_count > avgWords * 2 ? "long" : c.word_count < avgWords * 0.35 ? "short" : null) : null) as
      | "long"
      | "short"
      | null,
  }));

  // Who appears where.
  const appears = new Map<string, string[]>();
  for (const e of entities) {
    const forms = nameForms(e);
    appears.set(
      e.id,
      written.filter((c) => mentions(c.content, forms)).map((c) => c.id),
    );
  }
  const hasText = written.length > 0;
  const orphaned = hasText ? entities.filter((e) => !(appears.get(e.id) ?? []).length) : [];
  const thin = entities.filter((e) => e.description.trim().length < 30);

  // Likely duplicates: same name once articles and punctuation are ignored, or one is the other's alias.
  const duplicates: [Entity, Entity][] = [];
  for (let i = 0; i < entities.length; i++) {
    for (let j = i + 1; j < entities.length; j++) {
      const a = entities[i];
      const b = entities[j];
      const fa = new Set(nameForms(a).map(norm));
      if (nameForms(b).some((f) => fa.has(norm(f))) && a.category === b.category) duplicates.push([a, b]);
    }
  }

  const characters = entities.filter((e) => e.category === "Character");
  const cast = characters
    .map((e) => ({ entity: e, chapters: new Set(appears.get(e.id) ?? []) }))
    .filter((c) => c.chapters.size > 0)
    .sort((a, b) => b.chapters.size - a.chapters.size)
    .slice(0, 10);

  // A character seen in 2+ chapters who hasn't shown up in the last 3 written chapters.
  const vanished: Insights["vanished"] = [];
  if (written.length >= 5) {
    const recent = new Set(written.slice(-3).map((c) => c.id));
    for (const c of cast) {
      if (c.chapters.size >= 2 && ![...c.chapters].some((id) => recent.has(id))) {
        const last = [...written].reverse().find((w) => c.chapters.has(w.id));
        vanished.push({ entity: c.entity, lastSeen: last?.title || "an earlier chapter" });
      }
    }
  }

  const summaries = { have: written.filter((c) => c.summary.trim()).length, need: written.length };
  const outlineChapters = (project.outline.match(/^\s*chapter\s+\d+/gim) ?? []).length;
  const ruleCount = project.canon_rules.split("\n").filter((l) => l.trim()).length;

  const risks: Risk[] = [];
  if (summaries.need && summaries.have < summaries.need) {
    risks.push({
      level: summaries.need - summaries.have > 2 ? "high" : "medium",
      text: `${summaries.need - summaries.have} of ${summaries.need} chapters have no summary`,
      detail: "The AI uses chapter summaries as “the story so far”. Without them it can lose the thread.",
      target: "world",
    });
  }
  if (!project.outline.trim() && written.length) risks.push({ level: "medium", text: "No outline yet", detail: "MANTIS can build one from the chapters you have.", target: "plan" });
  if (outlineChapters > ordered.length) {
    risks.push({ level: "low", text: `Outline has ${outlineChapters} chapters; the book has ${ordered.length}`, detail: "Create the missing chapters from the Plan tab when you're ready.", target: "plan" });
  }
  if (hasText && !entities.length) risks.push({ level: "high", text: "The World Bible is empty", detail: "Scan your chapters so the AI knows your characters and places.", target: "world" });
  if (duplicates.length) {
    risks.push({ level: "medium", text: `${duplicates.length} possible duplicate World Bible ${duplicates.length === 1 ? "entry" : "entries"}`, detail: duplicates.slice(0, 3).map(([a, b]) => `${a.name} / ${b.name}`).join("; "), target: "world" });
  }
  if (orphaned.length) {
    risks.push({ level: "low", text: `${orphaned.length} World Bible ${orphaned.length === 1 ? "entry isn't" : "entries aren't"} in any chapter`, detail: orphaned.slice(0, 5).map((e) => e.name).join(", "), target: "world" });
  }
  if (thin.length) risks.push({ level: "low", text: `${thin.length} World Bible ${thin.length === 1 ? "entry has" : "entries have"} almost no notes`, detail: thin.slice(0, 5).map((e) => e.name).join(", "), target: "world" });
  for (const v of vanished.slice(0, 3)) {
    risks.push({ level: "low", text: `${v.entity.name} hasn't appeared since “${v.lastSeen}”`, detail: "Intentional? If not, bring them back or tie off their thread.", target: "write" });
  }
  const odd = lengths.filter((l) => l.flag);
  if (odd.length) {
    risks.push({ level: "low", text: `${odd.length} ${odd.length === 1 ? "chapter is" : "chapters are"} much longer or shorter than the rest`, detail: odd.slice(0, 4).map((l) => `${l.title} (${l.words.toLocaleString()})`).join(", "), target: "write" });
  }
  const empty = ordered.filter((c) => !c.word_count);
  if (empty.length && written.length) risks.push({ level: "low", text: `${empty.length} empty ${empty.length === 1 ? "chapter" : "chapters"}`, detail: empty.slice(0, 4).map((c) => c.title).join(", "), target: "write" });

  const readiness: Readiness[] = [
    { label: "Premise", ok: project.premise.trim().length >= 40, hint: "Who wants what, and what's in the way.", target: "plan" },
    { label: "Outline", ok: outlineChapters >= 3 || project.outline.trim().length >= 300, hint: "At least a few chapter beats.", target: "plan" },
    { label: "Canon rules", ok: ruleCount >= 3, hint: "Facts the AI must never contradict.", target: "plan" },
    { label: "Style guide", ok: project.style_guide.trim().length >= 20, hint: "POV, tense, voice.", target: "plan" },
    { label: "World Bible", ok: entities.length >= 5, hint: "Your main characters and places.", target: "world" },
    { label: "Chapter summaries", ok: summaries.need > 0 && summaries.have / summaries.need >= 0.8, hint: "So the AI remembers the story so far.", target: "world" },
  ];
  const readinessScore = Math.round((readiness.filter((r) => r.ok).length / readiness.length) * 100);

  let next: Insights["next"];
  if (!written.length && !project.premise.trim()) next = { text: "Write down your premise", why: "One paragraph is enough. Everything the AI does starts from it.", target: "plan", cta: "Open Plan" };
  else if (!written.length) next = { text: "Start Chapter 1", why: "Even 200 words gives MANTIS something to work with.", target: "write", cta: "Start writing" };
  else if (summaries.need - summaries.have > 2 || (hasText && !entities.length)) {
    next = { text: "Scan your chapters", why: "Fills in summaries and the World Bible so the AI keeps your story straight.", target: "world", cta: "Open World Bible" };
  } else if (!project.outline.trim()) next = { text: "Build an outline", why: "Use “From my chapters” on the Plan tab to map what you have and what comes next.", target: "plan", cta: "Open Plan" };
  else if (duplicates.length) next = { text: "Merge duplicate World Bible entries", why: "Two entries for one character confuse the AI.", target: "world", cta: "Open World Bible" };
  else if (readinessScore < 70) {
    const miss = readiness.find((r) => !r.ok)!;
    next = { text: `Add your ${miss.label.toLowerCase()}`, why: miss.hint, target: miss.target, cta: "Fix it" };
  } else {
    const last = written[written.length - 1];
    next = { text: `Keep going with “${last.title}”`, why: "Your book is in good shape. The best next step is more words.", target: "write", cta: "Write" };
  }

  return {
    totalWords,
    target,
    drafted: written.length,
    chapterCount: ordered.length,
    avgWords,
    lengths,
    summaries,
    outlineChapters,
    appears,
    orphaned,
    thin,
    duplicates,
    cast,
    vanished,
    risks: risks.sort((a, b) => ["high", "medium", "low"].indexOf(a.level) - ["high", "medium", "low"].indexOf(b.level)),
    readiness,
    readinessScore,
    next,
  };
}
