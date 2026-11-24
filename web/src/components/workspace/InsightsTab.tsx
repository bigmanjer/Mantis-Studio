"use client";
import { AlertTriangle, ArrowRight, CheckCircle2, Circle, Gauge, Loader2, Sparkles, Telescope } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { computeInsights, type InsightTarget } from "@/lib/insights";
import { createClient } from "@/lib/supabase/client";
import type { Chapter, Entity, Project } from "@/lib/types";
import { AiClientError, runAi } from "./aiClient";

type ReviewItem = { kind: string; chapter: string; issue: string; suggestion: string };

/**
 * Insights (ported from the original MANTIS app): what needs attention next, how ready the
 * book is for good AI help, who appears where, chapter balance and momentum. Instant and
 * free; the plot-hole read is the only part that uses AI.
 */
export default function InsightsTab({
  project,
  chapters,
  entities,
  aiContext,
  goTo,
}: {
  project: Project;
  chapters: Chapter[];
  entities: Entity[];
  aiContext: unknown;
  goTo: (tab: InsightTarget) => void;
}) {
  const supabase = createClient();
  const ins = useMemo(() => computeInsights(project, chapters, entities), [project, chapters, entities]);
  const [days, setDays] = useState<{ day: string; words: number }[] | null>(null);
  const [review, setReview] = useState<ReviewItem[] | null>(null);
  const [reviewing, setReviewing] = useState(false);
  const [reviewErr, setReviewErr] = useState("");

  useEffect(() => {
    const from = new Date(Date.now() - 13 * 86400000).toISOString().slice(0, 10);
    void supabase
      .from("writing_days")
      .select("day, words")
      .gte("day", from)
      .then(({ data }) => setDays((data ?? []) as { day: string; words: number }[]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const last14 = useMemo(() => {
    const map = new Map((days ?? []).map((d) => [d.day, d.words]));
    return Array.from({ length: 14 }, (_, i) => {
      const d = new Date(Date.now() - (13 - i) * 86400000);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      return { key, label: d.toLocaleDateString(undefined, { weekday: "narrow" }), date: d.toLocaleDateString(undefined, { month: "short", day: "numeric" }), words: map.get(key) ?? 0 };
    });
  }, [days]);
  const week = last14.slice(7).reduce((a, d) => a + d.words, 0);

  const ordered = [...chapters].sort((a, b) => a.position - b.position).filter((c) => c.word_count > 0);
  const maxLen = Math.max(1, ...ins.lengths.map((l) => l.words));
  const maxDay = Math.max(1, ...last14.map((d) => d.words));

  async function runReview() {
    setReviewing(true);
    setReviewErr("");
    try {
      const digest = ordered.map((c, i) => `Chapter ${i + 1}: ${c.title}\n${c.summary || c.content.slice(0, 1200)}`).join("\n\n");
      const raw = await runAi({ action: "review", text: digest, context: aiContext });
      const parsed = JSON.parse(raw.slice(raw.indexOf("["), raw.lastIndexOf("]") + 1)) as ReviewItem[];
      setReview(parsed.filter((r) => r && typeof r.issue === "string").slice(0, 8));
    } catch (e) {
      setReviewErr(e instanceof AiClientError ? e.message : "The read-through couldn't be completed. Please try again.");
    }
    setReviewing(false);
  }

  const pct = Math.min(100, Math.round((ins.totalWords / ins.target) * 100));
  const tiles = [
    { label: "Words", value: ins.totalWords.toLocaleString(), sub: `${pct}% of ${ins.target.toLocaleString()}` },
    { label: "Chapters drafted", value: `${ins.drafted} / ${ins.chapterCount}`, sub: ins.outlineChapters ? `${ins.outlineChapters} in the outline` : "no outline yet" },
    { label: "Average chapter", value: ins.avgWords.toLocaleString(), sub: "words" },
    { label: "World Bible", value: String(entities.length), sub: `${ins.cast.length} characters on the page` },
    { label: "This week", value: week.toLocaleString(), sub: "words you wrote (all books)" },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <h1 className="font-serif text-2xl font-semibold">Insights</h1>
      <p className="mt-1 text-sm text-muted">What needs attention, how ready the book is for AI help, and who shows up where. Updates as you write.</p>

      {/* Next best action */}
      <div className="mt-6 flex flex-wrap items-center gap-4 rounded-2xl border border-accent/40 bg-accent-soft/40 p-5">
        <Telescope size={22} className="shrink-0 text-accent" />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold tracking-wide text-accent uppercase">Next best step</p>
          <p className="mt-0.5 font-serif text-lg font-semibold">{ins.next.text}</p>
          <p className="text-sm text-muted">{ins.next.why}</p>
        </div>
        <button onClick={() => goTo(ins.next.target)} className="btn-primary">
          {ins.next.cta} <ArrowRight size={15} />
        </button>
      </div>

      {/* Stat tiles */}
      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {tiles.map((t) => (
          <div key={t.label} className="card p-4">
            <p className="text-xs text-muted">{t.label}</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums">{t.value}</p>
            <p className="text-[11px] text-muted">{t.sub}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        {/* Risk radar */}
        <section className="card p-5">
          <h2 className="flex items-center gap-2 font-semibold">
            <AlertTriangle size={16} className="text-accent" /> Things to look at
          </h2>
          {ins.risks.length === 0 ? (
            <p className="mt-3 flex items-center gap-2 text-sm text-muted">
              <CheckCircle2 size={16} className="text-accent" /> Nothing stands out. Your book is in good shape.
            </p>
          ) : (
            <ul className="mt-3 space-y-2">
              {ins.risks.map((r, i) => (
                <li key={i} className="flex items-start gap-3 rounded-xl border border-line bg-panel p-3">
                  <span
                    className={`mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                      r.level === "high" ? "bg-danger-soft text-danger" : r.level === "medium" ? "bg-accent-soft text-accent" : "bg-panel-3 text-muted"
                    }`}
                  >
                    {r.level === "high" ? "Fix soon" : r.level === "medium" ? "Worth a look" : "FYI"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{r.text}</p>
                    {r.detail && <p className="mt-0.5 text-xs text-muted">{r.detail}</p>}
                  </div>
                  <button onClick={() => goTo(r.target)} className="btn-quiet h-7 shrink-0 px-2 text-xs">
                    Open <ArrowRight size={12} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* AI readiness */}
        <section className="card h-fit p-5">
          <h2 className="flex items-center gap-2 font-semibold">
            <Gauge size={16} className="text-accent" /> AI readiness
          </h2>
          <p className="mt-1 text-xs text-muted">The more of this you have, the better the AI keeps to your story.</p>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-semibold tabular-nums">{ins.readinessScore}%</span>
            <span className="text-xs text-muted">{ins.readiness.filter((r) => r.ok).length} of {ins.readiness.length} in place</span>
          </div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-panel-3" role="progressbar" aria-valuenow={ins.readinessScore} aria-valuemin={0} aria-valuemax={100} aria-label="AI readiness">
            <div className="h-full rounded-full bg-accent" style={{ width: `${ins.readinessScore}%` }} />
          </div>
          <ul className="mt-3 space-y-1.5">
            {ins.readiness.map((r) => (
              <li key={r.label}>
                <button onClick={() => goTo(r.target)} className="flex w-full cursor-pointer items-start gap-2 rounded-lg px-1 py-0.5 text-left text-sm hover:bg-panel-2" title={r.hint}>
                  {r.ok ? <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-accent" /> : <Circle size={15} className="mt-0.5 shrink-0 text-muted" />}
                  <span className={r.ok ? "" : "text-muted"}>
                    {r.label}
                    {!r.ok && <span className="block text-[11px]">{r.hint}</span>}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      </div>

      {/* Who appears where */}
      <section className="card mt-6 p-5">
        <h2 className="font-semibold">Who appears where</h2>
        <p className="mt-1 text-xs text-muted">Characters from your World Bible, by the chapters that mention them. Gaps can be fine, or a thread you dropped.</p>
        {ins.cast.length === 0 || !ordered.length ? (
          <p className="mt-3 text-sm text-muted">This fills in once you have chapters and characters in the World Bible.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="border-separate border-spacing-[2px] text-xs">
              <thead>
                <tr>
                  <th className="sticky left-0 bg-panel pr-3 text-left font-normal text-muted">Character</th>
                  {ordered.map((c, i) => (
                    <th key={c.id} className="w-7 text-center font-normal text-muted tabular-nums" title={c.title}>
                      {i + 1}
                    </th>
                  ))}
                  <th className="pl-2 text-left font-normal text-muted">Chapters</th>
                </tr>
              </thead>
              <tbody>
                {ins.cast.map(({ entity, chapters: seen }) => (
                  <tr key={entity.id}>
                    <td className="sticky left-0 max-w-[160px] truncate bg-panel pr-3 font-medium">{entity.name}</td>
                    {ordered.map((c) => (
                      <td key={c.id} className="h-6 w-7 p-0" title={`${entity.name} ${seen.has(c.id) ? "appears in" : "is not in"} ${c.title}`}>
                        <span className={`block h-6 w-7 rounded-[4px] ${seen.has(c.id) ? "bg-accent" : "bg-panel-3"}`} aria-label={seen.has(c.id) ? "yes" : "no"} />
                      </td>
                    ))}
                    <td className="pl-2 text-muted tabular-nums">{seen.size}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Chapter lengths */}
        <section className="card p-5">
          <h2 className="font-semibold">Chapter lengths</h2>
          <p className="mt-1 text-xs text-muted">
            Words per chapter{ins.avgWords ? `; the line marks your average (${ins.avgWords.toLocaleString()})` : ""}. Outliers aren&apos;t wrong, just worth a second look.
          </p>
          {ins.lengths.length === 0 ? (
            <p className="mt-3 text-sm text-muted">No chapters yet.</p>
          ) : (
            <div className="relative mt-4 flex h-40 items-end gap-[2px]" role="img" aria-label="Words per chapter">
              {ins.avgWords > 0 && (
                <div className="pointer-events-none absolute inset-x-0 border-t border-dashed border-muted/50" style={{ bottom: `${(ins.avgWords / maxLen) * 100}%` }} />
              )}
              {ins.lengths.map((l, i) => (
                <div key={l.id} className="group relative flex h-full flex-1 items-end justify-center" title={`${l.title}: ${l.words.toLocaleString()} words`}>
                  <div
                    className={`w-full max-w-[28px] rounded-t-[4px] ${l.flag ? "bg-accent/45" : "bg-accent"}`}
                    style={{ height: `${Math.max(l.words ? 2 : 0, (l.words / maxLen) * 100)}%` }}
                  />
                  <span className="pointer-events-none absolute -top-6 left-1/2 hidden -translate-x-1/2 rounded bg-panel-3 px-1.5 py-0.5 text-[10px] whitespace-nowrap group-hover:block">
                    {i + 1}. {l.words.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Momentum */}
        <section className="card p-5">
          <h2 className="font-semibold">Your last two weeks</h2>
          <p className="mt-1 text-xs text-muted">Words you wrote yourself each day, across all your books (AI text doesn&apos;t count).</p>
          {days === null ? (
            <Loader2 size={16} className="mt-4 animate-spin text-muted" />
          ) : (
            <>
              <div className="mt-4 flex h-32 items-end gap-[2px]" role="img" aria-label="Words written per day, last 14 days">
                {last14.map((d) => (
                  <div key={d.key} className="group relative flex h-full flex-1 flex-col items-center justify-end" title={`${d.date}: ${d.words.toLocaleString()} words`}>
                    <div className={`w-full max-w-[28px] rounded-t-[4px] ${d.words ? "bg-accent" : "bg-panel-3"}`} style={{ height: `${d.words ? Math.max(3, (d.words / maxDay) * 100) : 3}%` }} />
                    <span className="pointer-events-none absolute -top-6 hidden rounded bg-panel-3 px-1.5 py-0.5 text-[10px] whitespace-nowrap group-hover:block">{d.words.toLocaleString()}</span>
                  </div>
                ))}
              </div>
              <div className="mt-1 flex gap-[2px] text-center text-[10px] text-muted">
                {last14.map((d) => (
                  <span key={d.key} className="flex-1">
                    {d.label}
                  </span>
                ))}
              </div>
            </>
          )}
        </section>
      </div>

      {/* AI read-through */}
      <section className="card mt-6 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="flex items-center gap-2 font-semibold">
              <Sparkles size={16} className="text-accent" /> Read-through for plot holes
            </h2>
            <p className="mt-1 text-xs text-muted">The AI reads your chapter summaries end to end, like a developmental editor, and lists what a reader would trip over.</p>
          </div>
          <button onClick={runReview} disabled={reviewing || ordered.length < 2} className="btn-primary">
            {reviewing ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
            {reviewing ? "Reading…" : review ? "Read again" : "Read my book"}
          </button>
        </div>
        {ordered.length < 2 && <p className="mt-3 text-sm text-muted">Write at least two chapters first.</p>}
        {reviewErr && <p className="mt-3 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{reviewErr}</p>}
        {review && review.length === 0 && <p className="mt-3 text-sm text-muted">No real problems found. Nice.</p>}
        {review && review.length > 0 && (
          <ul className="mt-4 space-y-2">
            {review.map((r, i) => (
              <li key={i} className="rounded-xl border border-line bg-panel p-3">
                <p className="text-[11px] tracking-wide text-accent uppercase">
                  {r.kind} · {r.chapter}
                </p>
                <p className="mt-1 text-sm">{r.issue}</p>
                <p className="mt-1 text-sm text-muted">
                  <span className="font-medium text-text/80">Try: </span>
                  {r.suggestion}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
