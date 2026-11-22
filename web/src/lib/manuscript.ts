import { countWords } from "./types";

export interface ParsedChapter {
  title: string;
  content: string;
  word_count: number;
}

const NUMBER_WORDS =
  "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty";

// A line is a chapter heading if it's short and looks like "Chapter 3", "CHAPTER THREE: The Fall",
// "Prologue", "Epilogue", "Part Two", or a Markdown heading.
const HEADING = new RegExp(
  String.raw`^\s*(?:#{1,3}\s+.+|(?:chapter|ch\.)\s+(?:\d+|[ivxlc]+|(?:${NUMBER_WORDS})(?:[- ](?:${NUMBER_WORDS}))?)\b.*|prologue\b.*|epilogue\b.*|interlude\b.*)\s*$`,
  "i",
);

function isHeading(line: string): boolean {
  const t = line.trim();
  if (!t || !HEADING.test(t)) return false;
  if (t.startsWith("#")) return t.length <= 120;
  // Real headings are short and don't read like a sentence.
  return t.length <= 80 && !/[.!?,;]["”’']?$/.test(t);
}

function cleanTitle(line: string): string {
  return line
    .replace(/^#{1,3}\s+/, "")
    .replace(/\*+/g, "")
    .trim()
    .slice(0, 200);
}

/** Split a manuscript's plain text into chapters by its headings. */
export function splitManuscript(raw: string): ParsedChapter[] {
  const text = raw.replace(/\r\n?/g, "\n").replace(/ /g, " ");
  const lines = text.split("\n");
  const chapters: { title: string; lines: string[] }[] = [];
  let current: { title: string; lines: string[] } | null = null;

  for (const line of lines) {
    if (isHeading(line)) {
      current = { title: cleanTitle(line), lines: [] };
      chapters.push(current);
    } else {
      if (!current) {
        // Text before the first heading (title page, epigraph, or a manuscript with no headings).
        if (!line.trim()) continue;
        current = { title: "Opening", lines: [] };
        chapters.push(current);
      }
      current.lines.push(line);
    }
  }

  const result = chapters
    .map((c) => {
      const content = c.lines.join("\n").replace(/\n{3,}/g, "\n\n").trim();
      return { title: c.title || "Untitled", content, word_count: countWords(content) };
    })
    // Drop tiny front matter (e.g. a title page) but never drop real chapters.
    .filter((c, i) => !(i === 0 && c.title === "Opening" && c.word_count < 60 && chapters.length > 1));

  if (result.length === 1 && result[0].title === "Opening") result[0].title = "Chapter 1";
  return result.slice(0, 300);
}
