"use client";
import { Check, Loader2, Sparkles, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import type { Chapter, Entity, Project } from "@/lib/types";
import { AiClientError, runAi } from "./aiClient";
import { scanChapters } from "./canonScan";

type Step = "world" | "plan" | "outline";
const STEPS: { id: Step; label: string }[] = [
  { id: "world", label: "Reading each chapter: World Bible, canon rules and summaries" },
  { id: "plan", label: "Filling in genre, premise and style guide" },
  { id: "outline", label: "Building the outline from your chapters" },
];

/**
 * After a manuscript import, organize the whole book automatically (the original MANTIS
 * "Import & Analyze"): World Bible, canon, chapter summaries, plan fields and outline.
 * Only empty fields are filled; nothing the writer wrote is replaced.
 */
export default function Organizer({
  project,
  setProject,
  chapters,
  setChapters,
  entities,
  setEntities,
  onClose,
}: {
  project: Project;
  setProject: React.Dispatch<React.SetStateAction<Project>>;
  chapters: Chapter[];
  setChapters: React.Dispatch<React.SetStateAction<Chapter[]>>;
  entities: Entity[];
  setEntities: React.Dispatch<React.SetStateAction<Entity[]>>;
  onClose: () => void;
}) {
  const supabase = createClient();
  const [step, setStep] = useState<Step | "done">("world");
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [error, setError] = useState("");
  const [summary, setSummary] = useState("");
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function run() {
    const ordered = [...chapters].sort((a, b) => a.position - b.position);
    const chapterSummaries: Record<string, string> = {};
    let canon = project.canon_rules;
    try {
      // 1. World Bible, canon rules and summaries, chapter by chapter.
      const totals = await scanChapters(
        supabase,
        project,
        ordered,
        entities,
        (text, context) => runAi({ action: "extract", text, context }),
        (s) => {
          setProgress({ done: s.done, total: s.total });
          setEntities(s.entities);
          canon = s.canon;
          setProject((prev) => ({ ...prev, canon_rules: s.canon }));
          Object.assign(chapterSummaries, s.summaries);
          setChapters((prev) => prev.map((c) => (s.summaries[c.id] ? { ...c, summary: s.summaries[c.id], summary_auto: true } : c)));
        },
      );

      // 2. Plan fields that are still empty.
      setStep("plan");
      const sample = ordered.map((c) => c.content).join("\n\n").slice(0, 6000);
      const raw = await runAi({ action: "autofill", text: sample, context: { project: { ...project, canon_rules: canon } } });
      const json = JSON.parse(raw.slice(raw.indexOf("{"), raw.lastIndexOf("}") + 1)) as Record<string, unknown>;
      const str = (v: unknown) => (Array.isArray(v) ? v.join("\n") : typeof v === "string" ? v.trim() : "");
      const patch: Partial<Project> = {};
      if (!project.genre.trim() && str(json.genre)) patch.genre = str(json.genre).slice(0, 100);
      if (!project.premise.trim() && str(json.premise)) patch.premise = str(json.premise).slice(0, 4000);
      if (!project.style_guide.trim() && str(json.style_guide)) patch.style_guide = str(json.style_guide).slice(0, 4000);
      if (!canon.trim() && str(json.canon_rules)) patch.canon_rules = str(json.canon_rules).slice(0, 4000);

      // 3. Outline from the chapters, if there isn't one.
      setStep("outline");
      if (!project.outline.trim()) {
        const digest = ordered
          .map((c, i) => `Chapter ${i + 1}: ${c.title}\n${chapterSummaries[c.id] || c.summary || c.content.slice(0, 900)}`)
          .join("\n\n");
        patch.outline = await runAi({ action: "reverse_outline", text: digest, context: { project: { ...project, ...patch, canon_rules: canon } } });
      }
      if (Object.keys(patch).length) {
        const { error: saveErr } = await supabase.from("projects").update(patch).eq("id", project.id);
        if (!saveErr) setProject((prev) => ({ ...prev, ...patch }));
      }
      setSummary(
        `${ordered.length} ${ordered.length === 1 ? "chapter" : "chapters"} organized: ${totals.added} World Bible ${totals.added === 1 ? "entry" : "entries"}, ${totals.facts} canon ${totals.facts === 1 ? "rule" : "rules"}${patch.outline ? ", an outline" : ""}${patch.premise ? " and a premise" : ""}. Everything is editable.`,
      );
      setStep("done");
    } catch (e) {
      setError(
        e instanceof AiClientError
          ? `${e.message} What was found so far has been saved.`
          : "Organizing stopped partway. What was found so far has been saved; you can scan again from the World Bible.",
      );
    }
  }

  const idx = step === "done" ? STEPS.length : STEPS.findIndex((s) => s.id === step);

  return (
    <div className="border-b border-line bg-accent-soft/40 px-4 py-3 sm:px-6" role="status" aria-live="polite">
      <div className="mx-auto flex max-w-6xl items-start gap-3">
        <Sparkles size={18} className="mt-0.5 shrink-0 text-accent" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold">{step === "done" ? "Your manuscript is organized" : error ? "Organizing paused" : "Organizing your manuscript…"}</p>
          {step === "done" ? (
            <p className="mt-0.5 text-sm text-muted">{summary}</p>
          ) : error ? (
            <p className="mt-0.5 text-sm text-danger">{error}</p>
          ) : (
            <ul className="mt-1.5 space-y-1 text-sm">
              {STEPS.map((s, i) => (
                <li key={s.id} className={`flex items-center gap-2 ${i > idx ? "text-muted/70" : i === idx ? "text-text" : "text-muted"}`}>
                  {i < idx ? <Check size={14} className="text-accent" /> : i === idx ? <Loader2 size={14} className="animate-spin text-accent" /> : <span className="h-3.5 w-3.5 rounded-full border border-line" />}
                  {s.label}
                  {s.id === "world" && i === idx && progress.total > 0 && <span className="text-muted">({progress.done} of {progress.total})</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
        {(step === "done" || error) && (
          <button onClick={onClose} className="btn-quiet h-8 w-8 shrink-0 p-0" aria-label="Close">
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
