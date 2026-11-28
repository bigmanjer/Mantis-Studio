"use client";
import { Check, Download, ImagePlus, Loader2, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ART_STYLES, fullPrompt } from "@/lib/art-styles";
import { COVER_FONTS, type CoverFont } from "@/lib/cover-fonts";
import { createClient } from "@/lib/supabase/client";
import type { Chapter, Project } from "@/lib/types";
import { AiClientError, runAi } from "./aiClient";

interface BookImage {
  id: string;
  kind: "cover" | "illustration";
  chapter_id: string | null;
  prompt: string;
  seed: number;
  width: number;
  height: number;
  caption: string;
}
interface CoverStyle {
  font: CoverFont;
  place: "top" | "bottom";
  tone: "light" | "dark";
  tagline: string;
}

// Amazon KDP's recommended ebook cover is 1600×2560 (1:1.6). Art is generated at 800×1280 and
// the downloadable cover is drawn at full size.
const COVER = { width: 800, height: 1280 };
const OUT = { width: 1600, height: 2560 };
const seed = () => Math.floor(Math.random() * 2_000_000_000);
const previewSrc = (prompt: string, s: number, w: number, h: number) =>
  `/api/image?${new URLSearchParams({ prompt, seed: String(s), width: String(w), height: String(h) })}`;

/**
 * Book art: a typeset cover (AI artwork + professional title layout, never AI-painted lettering)
 * and scene illustrations for picture books or illustrated editions.
 */
export default function ArtTab({
  project,
  setProject,
  chapters,
  aiContext,
}: {
  project: Project;
  setProject: React.Dispatch<React.SetStateAction<Project>>;
  chapters: Chapter[];
  aiContext: unknown;
}) {
  const supabase = createClient();
  const [images, setImages] = useState<BookImage[]>([]);
  const [style, setStyle] = useState<string>(/child|kid|picture/i.test(project.genre) ? "Picture book" : "Painted");
  const [direction, setDirection] = useState("");
  const [candidates, setCandidates] = useState<{ prompt: string; seed: number }[]>([]);
  const [painted, setPainted] = useState(0);
  const [paintedIll, setPaintedIll] = useState(0);
  const [busy, setBusy] = useState<"" | "cover" | "scenes" | "download">("");
  const [err, setErr] = useState("");
  const saved = (project.cover_style ?? {}) as Partial<CoverStyle>;
  const [cs, setCs] = useState<CoverStyle>({ font: saved.font ?? "Elegant", place: saved.place ?? "top", tone: saved.tone ?? "light", tagline: saved.tagline ?? "" });
  const ordered = useMemo(() => [...chapters].sort((a, b) => a.position - b.position), [chapters]);
  const [chapterId, setChapterId] = useState(ordered.find((c) => c.word_count > 0)?.id ?? ordered[0]?.id ?? "");
  const [count, setCount] = useState(3);

  useEffect(() => {
    void supabase
      .from("book_images")
      .select("id, kind, chapter_id, prompt, seed, width, height, caption")
      .eq("project_id", project.id)
      .order("created_at")
      .then(({ data }) => setImages((data ?? []) as BookImage[]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project.id]);

  const cover = images.find((i) => i.id === project.cover_id) ?? null;

  async function designCovers() {
    setBusy("cover");
    setErr("");
    try {
      const raw = await runAi({ action: "cover_prompt", text: ordered.map((c) => c.content).join("\n\n").slice(0, 3000), instruction: direction, context: aiContext });
      const prompt = (JSON.parse(raw.slice(raw.indexOf("{"), raw.lastIndexOf("}") + 1)) as { prompt?: string }).prompt?.trim();
      if (!prompt) throw new Error();
      const p = fullPrompt(prompt, style);
      setPainted(0);
      setCandidates(Array.from({ length: 4 }, () => ({ prompt: p, seed: seed() })));
    } catch (e) {
      setErr(e instanceof AiClientError ? e.message : "Couldn't design a cover just now. Please try again.");
    }
    setBusy("");
  }

  async function chooseCover(c: { prompt: string; seed: number }) {
    const { data, error } = await supabase
      .from("book_images")
      .insert({ project_id: project.id, user_id: project.user_id, kind: "cover", prompt: c.prompt, seed: c.seed, width: COVER.width, height: COVER.height })
      .select("id, kind, chapter_id, prompt, seed, width, height, caption")
      .single();
    if (error || !data) return setErr(error?.message ?? "Couldn't save that cover.");
    setImages((list) => [...list, data as BookImage]);
    await supabase.from("projects").update({ cover_id: data.id }).eq("id", project.id);
    setProject((p) => ({ ...p, cover_id: data.id }));
    setCandidates([]);
  }

  function updateStyle(patch: Partial<CoverStyle>) {
    const next = { ...cs, ...patch };
    setCs(next);
    setProject((p) => ({ ...p, cover_style: next }));
    void supabase.from("projects").update({ cover_style: next }).eq("id", project.id);
  }

  /** Draw the finished cover at KDP size: artwork, a soft scrim for legibility, then the typography. */
  async function downloadCover() {
    if (!cover) return;
    setBusy("download");
    setErr("");
    try {
      const img = new Image();
      img.src = `/api/image?id=${cover.id}`;
      await img.decode();
      const font = COVER_FONTS[cs.font];
      const family = font.family.replace(/var\([^)]+\),\s*/, "");
      await document.fonts.load(`${font.weight} 100px ${family}`);
      const canvas = document.createElement("canvas");
      canvas.width = OUT.width;
      canvas.height = OUT.height;
      const ctx = canvas.getContext("2d")!;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      const scale = Math.max(OUT.width / img.naturalWidth, OUT.height / img.naturalHeight);
      const w = img.naturalWidth * scale;
      const h = img.naturalHeight * scale;
      ctx.drawImage(img, (OUT.width - w) / 2, (OUT.height - h) / 2, w, h);
      const top = cs.place === "top";
      const shade = cs.tone === "light" ? "0,0,0" : "255,255,255";
      const grad = ctx.createLinearGradient(0, top ? 0 : OUT.height, 0, top ? OUT.height * 0.45 : OUT.height * 0.55);
      grad.addColorStop(0, `rgba(${shade},0.55)`);
      grad.addColorStop(1, `rgba(${shade},0)`);
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, OUT.width, OUT.height);
      ctx.fillStyle = cs.tone === "light" ? "#ffffff" : "#111111";
      ctx.textAlign = "center";
      ctx.shadowColor = cs.tone === "light" ? "rgba(0,0,0,0.45)" : "rgba(255,255,255,0.4)";
      ctx.shadowBlur = 18;
      const title = font.upper ? project.title.toUpperCase() : project.title;
      const lines = wrap(ctx, title, family, font.weight, 1360, 230);
      let size = lines.size;
      ctx.font = `${font.weight} ${size}px ${family}`;
      const startY = top ? 300 : OUT.height - 380 - (lines.lines.length - 1) * size * 1.05;
      lines.lines.forEach((l, i) => ctx.fillText(spaced(l, font.spacing), OUT.width / 2, startY + i * size * 1.05));
      if (cs.tagline.trim()) {
        size = 64;
        ctx.font = `italic 500 ${size}px ${family}`;
        ctx.fillText(cs.tagline.trim(), OUT.width / 2, top ? startY + lines.lines.length * lines.size * 1.05 + 30 : startY - lines.size - 10);
      }
      if (project.author.trim()) {
        ctx.font = `${font.weight} 96px ${family}`;
        const author = font.upper ? project.author.toUpperCase() : project.author;
        ctx.fillText(spaced(author, 0.12), OUT.width / 2, top ? OUT.height - 150 : 230);
      }
      const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, "image/jpeg", 0.92));
      if (!blob) throw new Error();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${project.title.replace(/[^\w\- ]+/g, "").trim() || "cover"}-cover-1600x2560.jpg`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      setErr("Couldn't build the cover file. Wait for the artwork to finish loading, then try again.");
    }
    setBusy("");
  }

  async function drawScenes() {
    const ch = ordered.find((c) => c.id === chapterId);
    if (!ch?.content.trim()) return setErr("Pick a chapter with some writing in it.");
    setBusy("scenes");
    setErr("");
    try {
      const raw = await runAi({ action: "scene_prompts", text: ch.content, words: count, instruction: direction, context: { ...(aiContext as object), chapterTitle: ch.title } });
      const scenes = (JSON.parse(raw.slice(raw.indexOf("["), raw.lastIndexOf("]") + 1)) as { caption?: string; prompt?: string }[]).filter((s) => s?.prompt).slice(0, count);
      if (!scenes.length) throw new Error();
      const square = style === "Picture book";
      const rows = scenes.map((s) => ({
        project_id: project.id,
        user_id: project.user_id,
        chapter_id: ch.id,
        kind: "illustration",
        prompt: fullPrompt(String(s.prompt), style),
        seed: seed(),
        width: square ? 1024 : 1152,
        height: square ? 1024 : 768,
        caption: String(s.caption ?? "").slice(0, 300),
      }));
      const { data, error } = await supabase.from("book_images").insert(rows).select("id, kind, chapter_id, prompt, seed, width, height, caption");
      if (error) throw error;
      setImages((list) => [...list, ...((data ?? []) as BookImage[])]);
    } catch (e) {
      setErr(e instanceof AiClientError ? e.message : "Couldn't plan the illustrations just now. Please try again.");
    }
    setBusy("");
  }

  async function redraw(img: BookImage) {
    const s = seed();
    const { error } = await supabase.from("book_images").update({ seed: s }).eq("id", img.id);
    if (!error) setImages((list) => list.map((i) => (i.id === img.id ? { ...i, seed: s } : i)));
  }

  async function remove(img: BookImage) {
    const { error } = await supabase.from("book_images").delete().eq("id", img.id);
    if (!error) setImages((list) => list.filter((i) => i.id !== img.id));
  }

  async function saveCaption(img: BookImage, caption: string) {
    setImages((list) => list.map((i) => (i.id === img.id ? { ...i, caption } : i)));
    await supabase.from("book_images").update({ caption }).eq("id", img.id);
  }

  const illustrations = images.filter((i) => i.kind === "illustration");
  const font = COVER_FONTS[cs.font];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <h1 className="font-serif text-2xl font-semibold">Book art</h1>
      <p className="mt-1 max-w-2xl text-sm text-muted">
        Cover artwork and illustrations made from your story. MANTIS sets your title in real book typography, so lettering is always crisp. Download a cover sized for Kindle, or add
        pictures to an illustrated edition.
      </p>

      <div className="mt-5 flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted">Art style</span>
        {Object.keys(ART_STYLES).map((s) => (
          <button key={s} onClick={() => setStyle(s)} className={`cursor-pointer rounded-full border px-3 py-1 text-sm transition ${style === s ? "border-accent bg-accent-soft text-accent" : "border-line text-muted hover:text-text"}`}>
            {s}
          </button>
        ))}
      </div>
      <input className="input mt-3 max-w-2xl" placeholder="Optional direction, e.g. “a lone figure on a cliff, storm coming in”" value={direction} onChange={(e) => setDirection(e.target.value)} />
      {err && <p className="mt-3 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{err}</p>}

      {/* Cover */}
      <section className="mt-6 grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <div>
          <div className="relative aspect-[5/8] overflow-hidden rounded-lg border border-line bg-panel-2 shadow-lg">
            {cover ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`/api/image?id=${cover.id}`} alt="Cover artwork" className="absolute inset-0 h-full w-full object-cover" />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-sm text-muted">Your cover appears here.</div>
            )}
            <div
              className="absolute inset-0"
              style={{
                background: `linear-gradient(${cs.place === "top" ? "180deg" : "0deg"}, rgba(${cs.tone === "light" ? "0,0,0" : "255,255,255"},0.55) 0%, rgba(0,0,0,0) 45%)`,
              }}
            />
            <div
              className={`absolute inset-x-0 px-5 text-center ${cs.place === "top" ? "top-[9%]" : "bottom-[12%]"}`}
              style={{ fontFamily: font.family, color: cs.tone === "light" ? "#fff" : "#111", textShadow: cs.tone === "light" ? "0 2px 10px rgba(0,0,0,.45)" : "0 1px 8px rgba(255,255,255,.4)" }}
            >
              <p style={{ fontWeight: font.weight, fontSize: project.title.length > 22 ? 26 : 34, lineHeight: 1.05, letterSpacing: `${font.spacing}em`, textTransform: font.upper ? "uppercase" : "none" }}>{project.title || "Untitled"}</p>
              {cs.tagline && <p className="mt-2 text-sm italic">{cs.tagline}</p>}
            </div>
            {project.author && (
              <p
                className={`absolute inset-x-0 text-center ${cs.place === "top" ? "bottom-[5%]" : "top-[8%]"}`}
                style={{ fontFamily: font.family, fontWeight: font.weight, fontSize: 15, letterSpacing: "0.12em", color: cs.tone === "light" ? "#fff" : "#111", textTransform: font.upper ? "uppercase" : "none" }}
              >
                {project.author}
              </p>
            )}
          </div>
          {cover && (
            <div className="mt-3 space-y-2 text-sm">
              <div className="flex flex-wrap gap-1.5">
                {(Object.keys(COVER_FONTS) as CoverFont[]).map((f) => (
                  <button key={f} onClick={() => updateStyle({ font: f })} className={`cursor-pointer rounded-md border px-2 py-1 text-xs ${cs.font === f ? "border-accent text-accent" : "border-line text-muted"}`} style={{ fontFamily: COVER_FONTS[f].family }}>
                    {f}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <select className="input py-1.5 text-sm" value={cs.place} onChange={(e) => updateStyle({ place: e.target.value as CoverStyle["place"] })} aria-label="Title position">
                  <option value="top">Title at top</option>
                  <option value="bottom">Title at bottom</option>
                </select>
                <select className="input py-1.5 text-sm" value={cs.tone} onChange={(e) => updateStyle({ tone: e.target.value as CoverStyle["tone"] })} aria-label="Text color">
                  <option value="light">Light text</option>
                  <option value="dark">Dark text</option>
                </select>
              </div>
              <input className="input py-1.5 text-sm" placeholder="Tagline (optional)" value={cs.tagline} onChange={(e) => updateStyle({ tagline: e.target.value.slice(0, 80) })} />
              {!project.author && <p className="text-xs text-muted">Add an author or pen name on the Plan tab to put it on the cover.</p>}
              <button onClick={() => void downloadCover()} disabled={busy === "download"} className="btn-primary w-full">
                {busy === "download" ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />} Download cover (1600 × 2560)
              </button>
            </div>
          )}
        </div>

        <div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">{cover ? "Try another cover" : "Design your cover"}</h2>
            <button onClick={() => void designCovers()} disabled={!!busy} className="btn-primary">
              {busy === "cover" ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />} {busy === "cover" ? "Designing…" : "Design 4 covers"}
            </button>
          </div>
          <p className="mt-1 text-xs text-muted">The AI reads your premise and opening, art-directs a cover for your genre, and paints four versions. Pictures take 5 to 20 seconds each.</p>
          {candidates.length > 0 && (
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {candidates.map((c, i) => (
                <figure key={c.seed} className="overflow-hidden rounded-lg border border-line bg-panel-2">
                  {/* The free image service paints one picture at a time, so options load in turn. */}
                  <QueuedImage
                    src={previewSrc(c.prompt, c.seed, COVER.width, COVER.height)}
                    ready={i <= painted}
                    onDone={() => setPainted((n) => Math.max(n, i + 1))}
                    className="aspect-[5/8] w-full object-cover"
                    alt="Cover option"
                  />
                  <button onClick={() => void chooseCover(c)} className="flex w-full cursor-pointer items-center justify-center gap-1 py-2 text-sm text-accent hover:bg-accent-soft">
                    <Check size={14} /> Use this
                  </button>
                </figure>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Illustrations */}
      <section className="mt-10">
        <h2 className="flex items-center gap-2 font-semibold">
          <ImagePlus size={17} className="text-accent" /> Illustrations
        </h2>
        <p className="mt-1 text-xs text-muted">For picture books and illustrated editions. MANTIS picks the most visual moments and keeps characters looking the same using your World Bible. They&apos;re included in the ebook export.</p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <select className="input w-auto py-1.5 text-sm" value={chapterId} onChange={(e) => setChapterId(e.target.value)} aria-label="Chapter">
            {ordered.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title || "Untitled"}
              </option>
            ))}
          </select>
          <select className="input w-auto py-1.5 text-sm" value={count} onChange={(e) => setCount(Number(e.target.value))} aria-label="How many pictures">
            {[1, 2, 3, 4].map((n) => (
              <option key={n} value={n}>
                {n} {n === 1 ? "picture" : "pictures"}
              </option>
            ))}
          </select>
          <button onClick={() => void drawScenes()} disabled={!!busy} className="btn-primary">
            {busy === "scenes" ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />} {busy === "scenes" ? "Planning…" : "Illustrate this chapter"}
          </button>
        </div>
        {illustrations.length === 0 ? (
          <p className="mt-4 text-sm text-muted">No illustrations yet.</p>
        ) : (
          ordered
            .filter((c) => illustrations.some((i) => i.chapter_id === c.id))
            .map((c) => (
              <div key={c.id} className="mt-5">
                <p className="text-sm font-medium">{c.title}</p>
                <div className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {illustrations
                    .filter((i) => i.chapter_id === c.id)
                    .map((img) => (
                      <figure key={img.id} className="overflow-hidden rounded-lg border border-line bg-panel">
                        <div style={{ aspectRatio: `${img.width} / ${img.height}` }} className="bg-panel-2">
                          <QueuedImage
                            key={img.seed}
                            src={`/api/image?id=${img.id}&s=${img.seed}`}
                            ready={illustrations.indexOf(img) <= paintedIll}
                            onDone={() => setPaintedIll((n) => Math.max(n, illustrations.indexOf(img) + 1))}
                            className="h-full w-full"
                            alt={img.caption || "Illustration"}
                          />
                        </div>
                        <figcaption className="space-y-2 p-2">
                          <input className="input py-1 text-xs" value={img.caption} onChange={(e) => void saveCaption(img, e.target.value.slice(0, 300))} placeholder="Caption" />
                          <div className="flex gap-2">
                            <button onClick={() => void redraw(img)} className="btn-ghost flex-1 py-1 text-xs">
                              <RefreshCw size={12} /> Redraw
                            </button>
                            <button onClick={() => void remove(img)} className="btn-quiet h-7 w-7 p-0" aria-label="Delete illustration">
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </figcaption>
                      </figure>
                    ))}
                </div>
              </div>
            ))
        )}
      </section>
    </div>
  );
}

/** Break a title into lines that fit, shrinking the type for long titles. */
function wrap(ctx: CanvasRenderingContext2D, text: string, family: string, weight: number, maxWidth: number, start: number) {
  for (let size = start; size >= 90; size -= 10) {
    ctx.font = `${weight} ${size}px ${family}`;
    const words = text.split(/\s+/);
    const lines: string[] = [];
    let line = "";
    for (const w of words) {
      const test = line ? `${line} ${w}` : w;
      if (ctx.measureText(test).width > maxWidth && line) {
        lines.push(line);
        line = w;
      } else line = test;
    }
    if (line) lines.push(line);
    if (lines.length <= 3 && lines.every((l) => ctx.measureText(l).width <= maxWidth)) return { lines, size };
  }
  return { lines: [text], size: 90 };
}

/** Letter-spacing for canvas text (not supported everywhere natively). */
function spaced(text: string, em: number) {
  return em > 0.05 ? text.split("").join(" ") : text;
}

/** An image that waits its turn, shows progress while painting, and offers a retry if it fails. */
function QueuedImage({ src, ready, onDone, className, alt }: { src: string; ready: boolean; onDone: () => void; className: string; alt: string }) {
  const [state, setState] = useState<"waiting" | "loading" | "done" | "failed">("waiting");
  const [attempt, setAttempt] = useState(0);
  const status = ready && state === "waiting" ? "loading" : state;
  return (
    <div className={`relative ${className}`}>
      {status !== "waiting" && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          key={attempt}
          src={attempt ? `${src}&r=${attempt}` : src}
          alt={alt}
          className={`h-full w-full object-cover ${status === "done" ? "" : "opacity-0"}`}
          onLoad={() => {
            setState("done");
            onDone();
          }}
          onError={() => {
            setState("failed");
            onDone();
          }}
        />
      )}
      {status !== "done" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-3 text-center text-xs text-muted">
          {status === "failed" ? (
            <>
              <span>The painter was busy.</span>
              <button
                onClick={() => {
                  setAttempt((a) => a + 1);
                  setState("loading");
                }}
                className="btn-ghost py-1 text-xs"
              >
                <RefreshCw size={12} /> Try again
              </button>
            </>
          ) : (
            <>
              <Loader2 size={16} className={status === "loading" ? "animate-spin" : ""} />
              {status === "loading" ? "Painting…" : "Waiting its turn…"}
            </>
          )}
        </div>
      )}
    </div>
  );
}
