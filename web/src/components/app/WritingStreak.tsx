"use client";
import { Flame, Pencil, Target } from "lucide-react";
import { useEffect, useMemo, useState, useTransition } from "react";
import { setDailyGoal } from "@/app/app/actions";
import { ProgressRing } from "@/components/ui/Progress";

const dayKey = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

/** Today's words vs. goal, current streak, and the last 7 days. Computed in the writer's own timezone. */
export default function WritingStreak({ days, goal: initialGoal }: { days: { day: string; words: number }[]; goal: number }) {
  const [goal, setGoal] = useState(initialGoal);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(String(initialGoal));
  const [err, setErr] = useState("");
  const [pending, start] = useTransition();

  // "Today" must be the writer's day, not the server's (UTC): only work it out in the browser.
  // Until then it renders empty, so server and browser output match (no hydration error).
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => setNow(new Date()), []);

  const { today, streak, week } = useMemo(() => {
    const byDay = new Map(days.map((d) => [d.day, d.words]));
    if (!now) return { today: 0, streak: 0, week: Array.from({ length: 7 }, (_, i) => ({ label: "", words: 0, isToday: i === 6 })) };
    const todayWords = byDay.get(dayKey(now)) ?? 0;
    // A streak counts consecutive days with any writing; today doesn't break it until it's over.
    let s = 0;
    const cursor = new Date(now);
    if (!todayWords) cursor.setDate(cursor.getDate() - 1);
    while ((byDay.get(dayKey(cursor)) ?? 0) > 0) {
      s++;
      cursor.setDate(cursor.getDate() - 1);
    }
    const w = Array.from({ length: 7 }, (_, i) => {
      const d = new Date(now);
      d.setDate(d.getDate() - (6 - i));
      return { label: d.toLocaleDateString(undefined, { weekday: "narrow" }), words: byDay.get(dayKey(d)) ?? 0, isToday: i === 6 };
    });
    return { today: todayWords, streak: s, week: w };
  }, [days, now]);

  const max = Math.max(goal, ...week.map((d) => d.words), 1);
  const pct = (today / goal) * 100;

  function save() {
    start(async () => {
      setErr("");
      const res = await setDailyGoal(Number(draft));
      if (res.error) setErr(res.error);
      else {
        setGoal(Number(draft));
        setEditing(false);
      }
    });
  }

  return (
    <div className="card grid gap-6 p-5 sm:grid-cols-[auto_1fr_auto] sm:items-center">
      <div className="flex items-center gap-4">
        <ProgressRing value={pct} size={64} stroke={6}>
          <span className="text-xs">{Math.min(999, Math.round(pct))}%</span>
        </ProgressRing>
        <div>
          <p className="flex items-center gap-1.5 text-xs text-muted">
            <Target size={13} className="text-accent" /> Today
          </p>
          <p className="text-xl font-semibold">
            {today.toLocaleString()}
            <span className="text-sm font-normal text-muted"> / {goal.toLocaleString()} words</span>
          </p>
          {editing ? (
            <div className="mt-1 flex items-center gap-2">
              <input
                type="number"
                min={50}
                max={20000}
                step={50}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                className="input w-24 py-1"
                aria-label="Daily word goal"
              />
              <button onClick={save} disabled={pending} className="btn-primary px-3 py-1 text-xs">
                Save
              </button>
              <button onClick={() => setEditing(false)} className="btn-quiet px-2 py-1 text-xs">
                Cancel
              </button>
            </div>
          ) : (
            <button onClick={() => setEditing(true)} className="mt-0.5 flex cursor-pointer items-center gap-1 text-xs text-muted hover:text-text">
              <Pencil size={11} /> Change daily goal
            </button>
          )}
          {err && <p className="mt-1 text-xs text-danger">{err}</p>}
        </div>
      </div>

      <div className="flex h-16 items-end gap-1.5" aria-label="Words written in the last 7 days">
        {week.map((d, i) => (
          <div key={i} className="flex flex-1 flex-col items-center gap-1" title={`${d.words.toLocaleString()} words`}>
            <div className="flex w-full flex-1 items-end">
              <div
                className={`w-full rounded-sm ${d.words >= goal ? "bg-accent" : d.words > 0 ? "bg-accent/45" : "bg-panel-3"}`}
                style={{ height: `${Math.max(6, (d.words / max) * 100)}%` }}
              />
            </div>
            <span className={`text-[10px] ${d.isToday ? "font-semibold text-text" : "text-muted"}`}>{d.label}</span>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3 sm:flex-col sm:items-end sm:gap-0">
        <p className="flex items-center gap-1.5 text-2xl font-semibold">
          <Flame size={20} className={streak > 0 ? "text-orange-400" : "text-muted"} /> {streak}
        </p>
        <p className="text-xs text-muted">day streak</p>
      </div>
    </div>
  );
}
