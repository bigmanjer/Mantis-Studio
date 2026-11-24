export interface WorldEntry {
  name: string;
  category: string;
  description: string;
  aliases?: string[];
}

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** True when any of the names appears in the text as a whole word (case-insensitive, Unicode-aware). */
export function mentions(text: string, names: string[]): boolean {
  return names.some((n) => {
    const name = n.trim();
    if (name.length < 2) return false;
    return new RegExp(`(^|[^\\p{L}\\p{N}])${escapeRe(name)}($|[^\\p{L}\\p{N}])`, "iu").test(text);
  });
}

/** Entries whose name or alias appears in the text. */
export function mentionedIn<T extends WorldEntry>(entities: T[], text: string): T[] {
  if (!text.trim()) return [];
  return entities.filter((e) => mentions(text, [e.name, ...(e.aliases ?? [])]));
}

const clip = (s: string | undefined, n: number) => (s ?? "").slice(0, n);

/**
 * World Bible block for a prompt. Entries named in the text being worked on come first with full
 * notes; the rest follow briefly. A large World Bible can't push the relevant characters out.
 */
export function worldBlock(entities: WorldEntry[], text: string): string {
  const hits = mentionedIn(entities, text).slice(0, 25);
  const hitSet = new Set(hits);
  const rest = entities.filter((e) => !hitSet.has(e)).slice(0, Math.max(0, 50 - hits.length));
  const line = (e: WorldEntry, n: number) => {
    const aka = e.aliases?.length ? ` (also: ${e.aliases.slice(0, 4).join(", ")})` : "";
    return `- ${e.name}${aka} [${e.category}]: ${clip(e.description, n)}`;
  };
  const parts: string[] = [];
  if (hits.length) parts.push(`IN THIS SCENE (from the World Bible):\n${hits.map((e) => line(e, 700)).join("\n")}`);
  if (rest.length) {
    parts.push(`${hits.length ? "OTHER WORLD BIBLE ENTRIES" : "WORLD BIBLE"}:\n${rest.map((e) => line(e, hits.length ? 120 : 200)).join("\n")}`);
  }
  return parts.join("\n\n");
}
