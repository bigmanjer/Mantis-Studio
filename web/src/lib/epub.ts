import "server-only";
import JSZip from "jszip";

export interface EpubBook {
  id: string;
  title: string;
  author: string;
  language?: string;
  description?: string;
  chapters: { title: string; content: string }[];
}

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** Plain manuscript text to XHTML paragraphs. A line of "***", "* * *" or "#" becomes a scene break. */
function toParagraphs(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .split(/\n\s*\n|\n/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => (/^(\*\s*){3,}$|^#$|^~+$/.test(p) ? `<p class="break">* * *</p>` : `<p>${esc(p)}</p>`))
    .join("\n");
}

const page = (title: string, body: string) => `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="UTF-8"/><title>${esc(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
${body}
</body>
</html>`;

const CSS = `body { font-family: Georgia, serif; line-height: 1.5; margin: 0 5%; }
h1 { text-align: center; font-weight: normal; margin: 3em 0 2em; page-break-before: always; }
p { margin: 0; text-indent: 1.5em; text-align: justify; }
h1 + p, p.break + p { text-indent: 0; }
p.break { text-align: center; text-indent: 0; margin: 1em 0; }
.title-page { text-align: center; margin-top: 30%; }
.title-page h1 { page-break-before: avoid; font-size: 2em; margin: 0 0 0.5em; }
.title-page p { text-indent: 0; text-align: center; font-style: italic; }`;

/** Build a valid EPUB 3 (with an EPUB 2 table of contents for older readers). */
export async function buildEpub(book: EpubBook): Promise<Uint8Array> {
  const zip = new JSZip();
  // The mimetype file must come first and be stored uncompressed.
  zip.file("mimetype", "application/epub+zip", { compression: "STORE" });
  zip.file(
    "META-INF/container.xml",
    `<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>`,
  );

  const lang = book.language || "en";
  const uid = `urn:uuid:${book.id}`;
  const modified = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  const chapters = book.chapters.filter((c) => c.content.trim() || c.title.trim());

  zip.file("OEBPS/style.css", CSS);
  zip.file(
    "OEBPS/title.xhtml",
    page(book.title, `<section class="title-page" epub:type="titlepage"><h1>${esc(book.title)}</h1>${book.author ? `<p>${esc(book.author)}</p>` : ""}</section>`),
  );
  chapters.forEach((c, i) => {
    zip.file(`OEBPS/ch${i + 1}.xhtml`, page(c.title || `Chapter ${i + 1}`, `<section epub:type="chapter"><h1>${esc(c.title || `Chapter ${i + 1}`)}</h1>\n${toParagraphs(c.content)}</section>`));
  });

  const navItems = chapters.map((c, i) => `<li><a href="ch${i + 1}.xhtml">${esc(c.title || `Chapter ${i + 1}`)}</a></li>`).join("\n");
  zip.file(
    "OEBPS/nav.xhtml",
    page("Contents", `<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>\n${navItems}\n</ol></nav>`),
  );
  zip.file(
    "OEBPS/toc.ncx",
    `<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="${uid}"/></head>
<docTitle><text>${esc(book.title)}</text></docTitle>
<navMap>
${chapters.map((c, i) => `<navPoint id="np${i + 1}" playOrder="${i + 1}"><navLabel><text>${esc(c.title || `Chapter ${i + 1}`)}</text></navLabel><content src="ch${i + 1}.xhtml"/></navPoint>`).join("\n")}
</navMap>
</ncx>`,
  );

  const manifest = [
    `<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>`,
    `<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>`,
    `<item id="css" href="style.css" media-type="text/css"/>`,
    `<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>`,
    ...chapters.map((_, i) => `<item id="ch${i + 1}" href="ch${i + 1}.xhtml" media-type="application/xhtml+xml"/>`),
  ].join("\n    ");
  const spine = [`<itemref idref="title"/>`, ...chapters.map((_, i) => `<itemref idref="ch${i + 1}"/>`)].join("\n    ");

  zip.file(
    "OEBPS/content.opf",
    `<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="${lang}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">${uid}</dc:identifier>
    <dc:title>${esc(book.title)}</dc:title>
    ${book.author ? `<dc:creator>${esc(book.author)}</dc:creator>` : ""}
    <dc:language>${lang}</dc:language>
    ${book.description ? `<dc:description>${esc(book.description.slice(0, 2000))}</dc:description>` : ""}
    <meta property="dcterms:modified">${modified}</meta>
  </metadata>
  <manifest>
    ${manifest}
  </manifest>
  <spine toc="ncx">
    ${spine}
  </spine>
</package>`,
  );

  return zip.generateAsync({ type: "uint8array", mimeType: "application/epub+zip", compression: "DEFLATE" });
}
