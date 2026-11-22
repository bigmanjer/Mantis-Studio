import { BookOpen, Feather, FileText, Sparkles } from "lucide-react";
import Link from "next/link";
import EmptyState from "@/components/ui/EmptyState";
import { ProgressBar } from "@/components/ui/Progress";
import { compact, coverFor, timeAgo } from "@/lib/format";
import ImportDialog from "./ImportDialog";
import NewProjectForm from "./NewProjectForm";

export interface ProjectSummary {
  id: string;
  title: string;
  genre: string;
  premise: string;
  target_words: number;
  updated_at: string;
  words: number;
  chapterCount: number;
}

export default function ProjectsView({
  projects,
  planName,
  maxProjects,
  email,
}: {
  projects: ProjectSummary[];
  planName: string;
  maxProjects: number;
  email: string;
}) {
  const atLimit = projects.length >= maxProjects;
  const totalWords = projects.reduce((a, p) => a + p.words, 0);
  const totalChapters = projects.reduce((a, p) => a + p.chapterCount, 0);
  const name = email.split("@")[0];
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const latest = projects[0];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted">
            {greeting}, {name}
          </p>
          <h1 className="mt-1 font-serif text-3xl font-semibold sm:text-4xl">Your projects</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <ImportDialog atLimit={atLimit} />
          <NewProjectForm atLimit={atLimit} planName={planName} />
        </div>
      </header>

      {projects.length > 0 && (
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {[
            { icon: BookOpen, label: "Projects", value: maxProjects === Infinity ? `${projects.length}` : `${projects.length} / ${maxProjects}` },
            { icon: FileText, label: "Chapters", value: compact(totalChapters) },
            { icon: Feather, label: "Words written", value: compact(totalWords) },
          ].map((s) => (
            <div key={s.label} className="card flex items-center gap-4 p-5">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
                <s.icon size={18} />
              </span>
              <div>
                <p className="text-xs text-muted">{s.label}</p>
                <p className="text-xl font-semibold">{s.value}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {latest && (
        <Link
          href={`/app/projects/${latest.id}`}
          className="group mt-6 flex items-center justify-between gap-4 rounded-2xl border border-accent/30 bg-accent-soft px-5 py-4 transition hover:border-accent/60"
        >
          <span className="flex items-center gap-3 text-sm">
            <Sparkles size={16} className="text-accent" />
            <span>
              Continue <span className="font-semibold">{latest.title}</span>
              <span className="text-muted"> · edited {timeAgo(latest.updated_at)}</span>
            </span>
          </span>
          <span className="text-sm font-medium text-accent transition group-hover:translate-x-0.5">Resume →</span>
        </Link>
      )}

      {projects.length === 0 ? (
        <div className="mt-10">
          <EmptyState
            icon={Feather}
            title="Every book starts with a blank page"
            body="Create your first project to outline the story, or import a manuscript you've already started."
            action={
              <div className="flex flex-wrap justify-center gap-2">
                <ImportDialog atLimit={false} />
                <NewProjectForm atLimit={false} planName={planName} />
              </div>
            }
          />
        </div>
      ) : (
        <div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {projects.map((p) => {
            const pct = (p.words / (p.target_words || 80000)) * 100;
            return (
              <Link
                key={p.id}
                href={`/app/projects/${p.id}`}
                className="group card flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:border-line-strong"
              >
                <div className="relative h-28 p-5" style={{ background: coverFor(p.id + p.title) }}>
                  <div className="absolute inset-0 bg-[linear-gradient(transparent,rgba(0,0,0,0.35))]" />
                  {p.genre && (
                    <span className="relative rounded-full bg-black/30 px-2.5 py-1 text-[11px] font-medium text-white/90 backdrop-blur">
                      {p.genre}
                    </span>
                  )}
                </div>
                <div className="flex flex-1 flex-col p-5">
                  <h2 className="font-serif text-lg leading-snug font-semibold group-hover:text-accent">{p.title}</h2>
                  <p className="mt-1.5 line-clamp-2 flex-1 text-sm text-muted">{p.premise || "No premise yet."}</p>
                  <ProgressBar value={pct} className="mt-5" />
                  <div className="mt-2 flex items-center justify-between text-xs text-muted">
                    <span>
                      {compact(p.words)} / {compact(p.target_words || 80000)} words
                    </span>
                    <span>{timeAgo(p.updated_at)}</span>
                  </div>
                </div>
              </Link>
            );
          })}
          <NewProjectForm atLimit={atLimit} planName={planName} variant="tile" />
        </div>
      )}
    </div>
  );
}
