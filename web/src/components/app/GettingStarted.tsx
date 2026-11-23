"use client";
import { Check, Loader2, Sparkles, X } from "lucide-react";
import { useEffect, useState, useTransition } from "react";
import { createSampleProject } from "@/app/app/actions";

export interface OnboardingState {
  hasProject: boolean;
  wrote100: boolean;
  usedAi: boolean;
  hasWorldEntry: boolean;
  atLimit: boolean;
}

const KEY = "mantis-onboarding-dismissed";

/** First-run checklist plus a one-click sample book. Hides itself when done or dismissed. */
export default function GettingStarted({ state }: { state: OnboardingState }) {
  const [dismissed, setDismissed] = useState(true);
  const [pending, start] = useTransition();
  const [err, setErr] = useState("");

  useEffect(() => {
    try {
      setDismissed(localStorage.getItem(KEY) === "1");
    } catch {
      setDismissed(false);
    }
  }, []);

  const steps = [
    { done: state.hasProject, label: "Create or import a book" },
    { done: state.wrote100, label: "Write your first 100 words" },
    { done: state.usedAi, label: "Ask the AI to continue a scene" },
    { done: state.hasWorldEntry, label: "Add a character or place to your World Bible" },
  ];
  const doneCount = steps.filter((s) => s.done).length;
  if (dismissed || doneCount === steps.length) return null;

  const dismiss = () => {
    setDismissed(true);
    try {
      localStorage.setItem(KEY, "1");
    } catch {
      /* fine: it just reappears next visit */
    }
  };

  return (
    <div className="card relative overflow-hidden p-5">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_80%_at_100%_0%,var(--accent-soft),transparent)]" />
      <div className="relative flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="flex items-center gap-2 font-semibold">
            <Sparkles size={16} className="text-accent" /> Getting started
            <span className="text-xs font-normal text-muted">
              {doneCount} of {steps.length}
            </span>
          </p>
          <ul className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            {steps.map((s) => (
              <li key={s.label} className={`flex items-center gap-2 ${s.done ? "text-muted line-through" : ""}`}>
                <span
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                    s.done ? "border-accent bg-accent text-accent-fg" : "border-line-strong"
                  }`}
                >
                  {s.done && <Check size={12} />}
                </span>
                {s.label}
              </li>
            ))}
          </ul>
        </div>
        <div className="flex items-center gap-2">
          {!state.atLimit && (
            <button
              onClick={() =>
                start(async () => {
                  setErr("");
                  const res = await createSampleProject();
                  if (res?.error) setErr(res.error);
                })
              }
              disabled={pending}
              className="btn-ghost"
            >
              {pending ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
              Try a sample book
            </button>
          )}
          <button onClick={dismiss} className="btn-quiet h-8 w-8 p-0" aria-label="Hide getting started">
            <X size={15} />
          </button>
        </div>
      </div>
      {err && <p className="relative mt-3 text-sm text-danger">{err}</p>}
    </div>
  );
}
