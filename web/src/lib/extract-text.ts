import "server-only";

/** File types the importer understands. Headings come back as "# Title" lines so chapters can be found. */
export const IMPORT_EXTENSIONS = ["docx", "doc", "pdf", "rtf", "odt", "epub", "html", "htm", "md", "markdown", "txt", "text", "fountain"] as const;

const ENTITIES: Record<string, string> = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ", rsquo: "’", lsquo: "‘", rdquo: "”", ldquo: "“", mdash: "—", ndash: "–", hellip: "…" };

function decodeEntities(s: string): string {
  return s.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e: string) => {
    if (e[0] === "#") {
      const code = e[1].toLowerCase() === "x" ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
      return Number.isFinite(code) ? String.fromCodePoint(code) : m;
    }
    return ENTITIES[e.toLowerCase()] ?? m;
  });
}

/** HTML or XHTML to plain text, keeping headings as "# " lines and paragraphs as blank-line breaks. */
export function htmlToText(html: string): string {
  return decodeEntities(
    html
      .replace(/<(script|style|head)[\s\S]*?<\/\1>/gi, "")
      .replace(/<h[1-3][^>]*>([\s\S]*?)<\/h[1-3]>/gi, (_, t: string) => `\n\n# ${t.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim()}\n\n`)
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/(p|div|li|blockquote|h[4-6]|tr|section)>/gi, "\n\n")
      .replace(/<hr[^>]*>/gi, "\n\n* * *\n\n")
      .replace(/<[^>]+>/g, ""),
  )
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

// RTF stores accented letters and curly quotes as Windows-1252 bytes (\'92 is ’).
const cp1252 = new TextDecoder("windows-1252");

/** Minimal RTF reader: drops control words and groups like fonts and colors, keeps the text. */
function rtfToText(rtf: string): string {
  let s = rtf.replace(/\{\\\*[^{}]*\}/g, "").replace(/\{\\(fonttbl|colortbl|stylesheet|info|pict)[\s\S]*?\}\s*(?=\{|\\|[^{}\\])/g, "");
  s = s
    .replace(/\\par[d]?\b ?/g, "\n")
    .replace(/\\line\b ?/g, "\n")
    .replace(/\\tab\b ?/g, "\t")
    .replace(/\\'([0-9a-f]{2})/gi, (_, h: string) => cp1252.decode(new Uint8Array([parseInt(h, 16)])))
    .replace(/\\u(-?\d+)\??/g, (_, n: string) => String.fromCharCode((Number(n) + 65536) % 65536))
    .replace(/\\[a-z]+-?\d* ?/gi, "")
    .replace(/[{}]/g, "")
    .replace(/\\([\\{}])/g, "$1");
  return s.replace(/\n{3,}/g, "\n\n").trim();
}

/** Text from an old binary .doc: keep long runs of readable characters. Best effort only. */
function legacyDocToText(buf: Buffer): string {
  const text = buf.toString("latin1").replace(/[^\x20-\x7E\xA0-\xFF\r\n\t]+/g, "\n");
  return text
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 25 && /[a-z]{3,}/i.test(l) && (l.match(/ /g) ?? []).length >= 3)
    .join("\n\n");
}

async function zipText(buf: Buffer, kind: "odt" | "epub"): Promise<string> {
  const JSZip = (await import("jszip")).default;
  const zip = await JSZip.loadAsync(buf);
  if (kind === "odt") {
    const xml = (await zip.file("content.xml")?.async("string")) ?? "";
    return htmlToText(
      xml
        .replace(/<text:h[^>]*>([\s\S]*?)<\/text:h>/g, "<h2>$1</h2>")
        .replace(/<text:p[^>]*>([\s\S]*?)<\/text:p>/g, "<p>$1</p>")
        .replace(/<text:line-break\/>/g, "<br/>")
        .replace(/<text:s[^>]*\/>/g, " ")
        .replace(/<text:tab\/>/g, "\t"),
    );
  }
  // EPUB: read the files in reading order (the spine of the package document).
  const container = (await zip.file("META-INF/container.xml")?.async("string")) ?? "";
  const opfPath = /full-path="([^"]+)"/.exec(container)?.[1] ?? "";
  const opf = (await zip.file(opfPath)?.async("string")) ?? "";
  const base = opfPath.includes("/") ? opfPath.slice(0, opfPath.lastIndexOf("/") + 1) : "";
  const manifest = new Map<string, string>();
  for (const m of opf.matchAll(/<item\b[^>]*>/g)) {
    const id = /\bid="([^"]+)"/.exec(m[0])?.[1];
    const href = /\bhref="([^"]+)"/.exec(m[0])?.[1];
    if (id && href) manifest.set(id, decodeURIComponent(href));
  }
  const order = [...opf.matchAll(/<itemref\b[^>]*idref="([^"]+)"/g)].map((m) => manifest.get(m[1])).filter(Boolean) as string[];
  const parts: string[] = [];
  for (const href of order) {
    if (/nav|toc|cover|title|copyright/i.test(href)) continue;
    const html = (await zip.file(base + href)?.async("string")) ?? "";
    const text = htmlToText(html);
    if (text) parts.push(text);
  }
  return parts.join("\n\n");
}

/** Pull readable text out of an uploaded manuscript. Throws a writer-friendly Error when it can't. */
export async function extractText(file: File): Promise<string> {
  const ext = file.name.toLowerCase().split(".").pop() ?? "";
  const buf = Buffer.from(await file.arrayBuffer());
  switch (ext) {
    case "docx": {
      // Convert through HTML so styled headings ("Heading 1") become chapter breaks.
      const mammoth = await import("mammoth");
      const { value } = await mammoth.convertToHtml({ buffer: buf });
      return htmlToText(value);
    }
    case "doc":
      return legacyDocToText(buf);
    case "pdf": {
      const { extractText: pdfText, getDocumentProxy } = await import("unpdf");
      const pdf = await getDocumentProxy(new Uint8Array(buf));
      const { text } = await pdfText(pdf, { mergePages: false });
      // Join pages, then rejoin lines that were only wrapped by the page layout.
      return (Array.isArray(text) ? text : [text])
        .join("\n\n")
        .replace(/-\n(?=[a-z])/g, "")
        .replace(/([^\n.!?:"”’)])\n(?=[a-z])/g, "$1 ")
        .replace(/^\s*\d+\s*$/gm, "");
    }
    case "rtf":
      return rtfToText(buf.toString("latin1"));
    case "odt":
      return zipText(buf, "odt");
    case "epub":
      return zipText(buf, "epub");
    case "html":
    case "htm":
      return htmlToText(buf.toString("utf8"));
    default:
      return buf.toString("utf8");
  }
}
