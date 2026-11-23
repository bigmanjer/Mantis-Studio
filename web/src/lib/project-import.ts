import { countWords, ENTITY_CATEGORIES, type EntityCategory } from "./types";

export interface ImportedBook {
  project: {
    title: string;
    author: string;
    genre: string;
    premise: string;
    outline: string;
    canon_rules: string;
    style_guide: string;
    target_words: number;
    style_dials: Record<string, number> | null;
  };
  chapters: { title: string; content: string; summary: string; word_count: number }[];
  entities: { name: string; category: EntityCategory; description: string; aliases: string[] }[];
}

const str = (v: unknown, max = 100_000) => (typeof v === "string" ? v : "").slice(0, max);
const cat = (v: unknown): EntityCategory => {
  const s = str(v).trim().toLowerCase();
  const hit = ENTITY_CATEGORIES.find((c) => c.toLowerCase() === s || c.toLowerCase() + "s" === s);
  if (hit) return hit;
  if (/char|person|people|npc/.test(s)) return "Character";
  if (/place|loc|setting|city|world/.test(s)) return "Location";
  if (/item|object|artifact|weapon/.test(s)) return "Item";
  if (/faction|group|org|guild|house/.test(s)) return "Faction";
  return "Lore";
};
const dials = (v: unknown): Record<string, number> | null => {
  if (!v || typeof v !== "object") return null;
  const out: Record<string, number> = {};
  for (const [k, val] of Object.entries(v as Record<string, unknown>)) {
    const n = Number(val);
    if (Number.isFinite(n)) out[k.toLowerCase()] = Math.max(0, Math.min(100, Math.round(n)));
  }
  return Object.keys(out).length ? out : null;
};

/**
 * Parse a MANTIS backup: either this website's `.mantis.json` backup, or a project file from
 * the original MANTIS Studio (Streamlit) app, whose chapters/world_db are keyed objects.
 */
export function parseProjectJson(text: string): ImportedBook {
  const data = JSON.parse(text) as Record<string, unknown>;

  if (data && data.mantis_web) {
    const p = (data.project ?? {}) as Record<string, unknown>;
    const chapters = (Array.isArray(data.chapters) ? data.chapters : []) as Record<string, unknown>[];
    const entities = (Array.isArray(data.entities) ? data.entities : []) as Record<string, unknown>[];
    return {
      project: {
        title: str(p.title, 200) || "Imported book",
        author: str(p.author, 200),
        genre: str(p.genre, 100),
        premise: str(p.premise, 5000),
        outline: str(p.outline),
        canon_rules: str(p.canon_rules, 10_000),
        style_guide: str(p.style_guide, 10_000),
        target_words: Number(p.target_words) > 0 ? Math.round(Number(p.target_words)) : 80000,
        style_dials: dials(p.style_dials),
      },
      chapters: chapters.map((c) => {
        const content = str(c.content);
        return { title: str(c.title, 200) || "Untitled", content, summary: str(c.summary, 5000), word_count: countWords(content) };
      }),
      entities: entities
        .filter((e) => str(e.name).trim())
        .map((e) => ({
          name: str(e.name, 200).trim(),
          category: cat(e.category),
          description: str(e.description, 20_000),
          aliases: Array.isArray(e.aliases) ? e.aliases.map((a) => str(a, 200)).filter(Boolean) : [],
        })),
    };
  }

  // Original MANTIS Studio (Streamlit) project file.
  if (data && (data.chapters || data.world_db) && typeof data.title === "string") {
    const chaptersObj = (data.chapters ?? {}) as Record<string, Record<string, unknown>>;
    const worldObj = (data.world_db ?? {}) as Record<string, Record<string, unknown>>;
    const chapters = Object.values(chaptersObj)
      .sort((a, b) => Number(a.index ?? 0) - Number(b.index ?? 0))
      .map((c) => {
        const content = str(c.content);
        return { title: str(c.title, 200) || "Untitled", content, summary: str(c.summary, 5000), word_count: countWords(content) };
      });
    const hard = str(data.memory_hard) || str(data.memory);
    const guidance = [str(data.style_guide), str(data.memory_soft), str(data.author_note)].filter((s) => s.trim()).join("\n\n");
    return {
      project: {
        title: str(data.title, 200) || "Imported book",
        author: str(data.author, 200),
        genre: str(data.genre, 100),
        premise: "",
        outline: str(data.outline),
        canon_rules: hard.slice(0, 10_000),
        style_guide: guidance.slice(0, 10_000),
        target_words: 80000,
        style_dials: dials(data.style_lens_settings),
      },
      chapters,
      entities: Object.values(worldObj)
        .filter((e) => str(e.name).trim())
        .map((e) => ({
          name: str(e.name, 200).trim(),
          category: cat(e.category),
          description: str(e.description, 20_000),
          aliases: Array.isArray(e.aliases) ? e.aliases.map((a) => str(a, 200)).filter(Boolean) : [],
        })),
    };
  }

  throw new Error("Not a MANTIS project file");
}
