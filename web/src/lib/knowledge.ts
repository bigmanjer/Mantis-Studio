import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { AUTHOR_LENSES, BUILTIN_ENTRIES, type AuthorLens } from "@/data/knowledge-builtin";

/**
 * Knowledge Base (ported from the original MANTIS app): a built-in craft library, author style
 * lenses, and the writer's own reference documents. The AI gets the few passages that matter
 * for the request; World Bible and canon rules stay in charge of story facts.
 */

export interface KnowledgeHit {
  source: "builtin" | "mine";
  title: string;
  category: string;
  text: string;
  docId?: string;
  score: number;
}

const STOP = new Set(
  "about after again also because been before between chapter could every from have into more than that their them then there these they this through under were with would your what when where which while will just like said very much some what over only even back".split(" "),
);

export function queryTerms(text: string, max = 24): string[] {
  const counts = new Map<string, number>();
  for (const w of (text.toLowerCase().match(/[a-z][a-z'-]{2,}/g) ?? []).map((w) => w.replace(/'s$/, ""))) {
    if (w.length < 4 || STOP.has(w)) continue;
    counts.set(w, (counts.get(w) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, max).map(([w]) => w);
}

/** Keyword search over the built-in library (same scoring idea as the original app). */
export function searchBuiltin(query: string, limit = 6, category?: string): KnowledgeHit[] {
  const terms = queryTerms(query);
  if (!terms.length) return [];
  const scored: KnowledgeHit[] = [];
  for (const e of BUILTIN_ENTRIES) {
    if (category && e.c !== category) continue;
    const hay = `${e.s} ${e.c} ${e.t}`.toLowerCase();
    let score = 0;
    for (const term of terms) {
      const hits = hay.split(term).length - 1;
      if (hits) score += Math.min(4, 1 + hits * 0.35);
      if (e.c === term || e.s.toLowerCase().includes(term)) score += 1.5;
    }
    if (score > 0) scored.push({ source: "builtin", title: e.s, category: e.c, text: e.t, score });
  }
  return scored.sort((a, b) => b.score - a.score).slice(0, limit);
}

/** Full-text search over the writer's own documents (Postgres, row-level security applies). */
export async function searchMine(supabase: SupabaseClient, projectId: string | null, query: string, limit = 6): Promise<KnowledgeHit[]> {
  const terms = queryTerms(query, 16);
  if (!terms.length) return [];
  const { data, error } = await supabase.rpc("search_knowledge", { p_query: terms.join(" or "), p_project: projectId, p_limit: limit });
  if (error || !data) return [];
  return (data as { doc_id: string; title: string; category: string; content: string; rank: number }[]).map((r) => ({
    source: "mine",
    title: r.title,
    category: r.category,
    text: r.content,
    docId: r.doc_id,
    score: r.rank,
  }));
}

/** Split a document into ~1,100-character passages on paragraph boundaries. */
export function chunkText(text: string, max = 1100): string[] {
  const paras = text
    .replace(/\r\n?/g, "\n")
    .split(/\n\s*\n|\n(?=#)/)
    .map((p) => p.replace(/[ \t]+/g, " ").trim())
    .filter(Boolean);
  const out: string[] = [];
  let cur = "";
  for (const p of paras) {
    if (p.length > max) {
      if (cur) {
        out.push(cur);
        cur = "";
      }
      // Very long paragraph: cut at sentence ends.
      let buf = "";
      for (const s of p.split(/(?<=[.!?])\s+/)) {
        if ((buf + " " + s).length > max && buf) {
          out.push(buf.trim());
          buf = "";
        }
        buf += " " + s;
      }
      if (buf.trim()) out.push(buf.trim());
      continue;
    }
    if ((cur + "\n\n" + p).length > max && cur) {
      out.push(cur);
      cur = "";
    }
    cur = cur ? `${cur}\n\n${p}` : p;
  }
  if (cur) out.push(cur);
  // Text with no sentence breaks (lists, PDF dumps): hard-wrap at spaces so no passage is huge.
  return out
    .flatMap((c) => {
      if (c.length <= max * 1.5) return [c];
      const pieces: string[] = [];
      let rest = c;
      while (rest.length > max) {
        const cut = rest.lastIndexOf(" ", max) > max / 2 ? rest.lastIndexOf(" ", max) : max;
        pieces.push(rest.slice(0, cut).trim());
        rest = rest.slice(cut).trim();
      }
      if (rest) pieces.push(rest);
      return pieces;
    })
    .slice(0, 2000);
}

/** Rough category for a document, from its words. */
export function classifyText(text: string): string {
  const low = text.toLowerCase().slice(0, 20000);
  const rules: [string, string[]][] = [
    ["research", ["according to", "historical", "century", "source:", "citation", "et al", "museum", "archive"]],
    ["style", ["style", "sentence", "voice", "tone", "prose", "pacing", "dialogue"]],
    ["worldbuilding", ["magic system", "kingdom", "religion", "economy", "map", "language", "culture", "technology"]],
    ["character", ["backstory", "motivation", "personality", "appearance", "arc"]],
    ["plot", ["act one", "act two", "beat", "outline", "inciting", "climax", "plot"]],
  ];
  let best = "reference";
  let bestScore = 0;
  for (const [cat, needles] of rules) {
    const score = needles.reduce((a, n) => a + (low.split(n).length - 1), 0);
    if (score > bestScore) {
      best = cat;
      bestScore = score;
    }
  }
  return bestScore >= 2 ? best : "reference";
}

export function findLenses(names: string[]): AuthorLens[] {
  const want = new Set(names.map((n) => n.toLowerCase()));
  return AUTHOR_LENSES.filter((a) => want.has(a.name.toLowerCase())).slice(0, 3);
}

/** Suggest author style lenses that fit the book (genre, premise, style guide, sample text). */
export function suggestLenses(bookText: string, limit = 6): (AuthorLens & { why: string[] })[] {
  const terms = new Set(queryTerms(bookText, 60));
  if (!terms.size) return [];
  return AUTHOR_LENSES.map((a) => {
    const traitWords = queryTerms(`${a.traits} ${a.works}`, 40);
    const why = traitWords.filter((w) => terms.has(w));
    return { ...a, why, score: why.length };
  })
    .filter((a) => a.score > 0)
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
    .slice(0, limit)
    .map((a) => ({ name: a.name, works: a.works, traits: a.traits, why: a.why }));
}

/**
 * Reference notes for a prompt: the writer's own documents first, then the built-in library,
 * plus any chosen style lenses. Returns "" when nothing relevant is found.
 */
export async function knowledgeBlock(
  supabase: SupabaseClient,
  opts: { projectId: string | null; query: string; lenses: string[]; useLibrary: boolean },
): Promise<string> {
  const parts: string[] = [];
  if (opts.useLibrary && opts.query.trim()) {
    const [mine, builtin] = await Promise.all([searchMine(supabase, opts.projectId, opts.query, 3), Promise.resolve(searchBuiltin(opts.query, 2))]);
    const hits = [...mine, ...builtin].slice(0, 4);
    if (hits.length) {
      parts.push(
        `REFERENCE NOTES (from the writer's Knowledge Base: guidance and research, not story canon; the World Bible and canon rules win any conflict):\n${hits
          .map((h) => `- [${h.source === "mine" ? h.title : h.category}] ${h.text.slice(0, 700)}`)
          .join("\n")}`,
      );
    }
  }
  const lenses = findLenses(opts.lenses);
  if (lenses.length) {
    parts.push(
      `STYLE LENSES (adapt these craft traits into the author's own voice; never copy passages or imitate a living author's prose):\n${lenses
        .map((l) => `- ${l.name} (${l.works}): ${l.traits}`)
        .join("\n")}`,
    );
  }
  return parts.join("\n\n");
}
