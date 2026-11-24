export interface WorldEntry {
  name: string;
  category: string;
  description: string;
  aliases?: string[];
}

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const ARTICLE = /^(the|a|an)\s+/i;
const HONORIFIC = /^(old|young|little|mr|mrs|ms|miss|dr|doctor|lady|lord|sir|dame|captain|capt|father|mother|sister|brother|aunt|uncle|king|queen|prince|princess|master|mistress)\.?\s+/i;

/**
 * Every way the text might refer to an entry: its name and aliases, the name without "the"/"a",
 * and for characters the first name without a title ("Old Agnes Pell" is also "Agnes").
 */
export function nameForms(e: WorldEntry): string[] {
  const forms = new Set<string>();
  for (const raw of [e.name, ...(e.aliases ?? [])]) {
    const n = raw.trim();
    if (!n) continue;
    forms.add(n);
    const bare = n.replace(ARTICLE, "");
    if (bare.length >= 3) forms.add(bare);
    if (e.category === "Character") {
      const first = bare.replace(HONORIFIC, "").split(/\s+/)[0];
      if (first && first.length >= 3 && /^\p{Lu}/u.test(first)) forms.add(first);
    }
  }
  return [...forms];
}

/** True when any of the names appears in the text as a whole word (case-insensitive, Unicode-aware). */
export function mentions(text: string, names: string[]): boolean {
  return names.some((n) => {
    const name = n.trim();
    if (name.length < 2) return false;
    return new RegExp(`(^|[^\\p{L}\\p{N}])${escapeRe(name)}($|[^\\p{L}\\p{N}])`, "iu").test(text);
  });
}

/** Entries whose name, alias or short form appears in the text. */
export function mentionedIn<T extends WorldEntry>(entities: T[], text: string): T[] {
  if (!text.trim()) return [];
  return entities.filter((e) => mentions(text, nameForms(e)));
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

const STOP = new Set(
  "a an the and or but of in on at to for with by from is was were be been her his their its it she he they them as that this who which has had have not year years old age aged".split(" "),
);

const UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"];
const TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];

/** "twenty-nine" → "29", "eleven" → "11", so "Ivy is 29" and "Ivy is twenty-nine" read as the same fact. */
function numbersToDigits(s: string): string {
  return s
    .replace(/\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)[\s-](one|two|three|four|five|six|seven|eight|nine)\b/gi, (_, t: string, u: string) =>
      String(TENS.indexOf(t.toLowerCase()) * 10 + UNITS.indexOf(u.toLowerCase())),
    )
    .replace(/\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\b/gi, (t) => String(TENS.indexOf(t.toLowerCase()) * 10))
    .replace(new RegExp(`\\b(${UNITS.join("|")})\\b`, "gi"), (u) => String(UNITS.indexOf(u.toLowerCase())));
}

/** Content words of a sentence, for "is this the same fact said differently?" checks. */
export function contentWords(s: string): Set<string> {
  return new Set(
    numbersToDigits(s.toLowerCase())
      .replace(/[^\p{L}\p{N}\s]/gu, " ")
      .split(/\s+/)
      .map((w) => w.replace(/(ing|ed|es|s)$/, ""))
      .filter((w) => (/^\d+$/.test(w) ? true : w.length > 2) && !STOP.has(w)),
  );
}

/** Share of the new sentence's content words already present in the existing one (0 to 1). */
export function overlap(newer: string, existing: string): number {
  const a = contentWords(newer);
  if (!a.size) return 1;
  const b = contentWords(existing);
  let hit = 0;
  for (const w of a) if (b.has(w)) hit++;
  return hit / a.size;
}
