"use client";
import { ArrowLeft, BookMarked, Download, ListTree, PenLine } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import Logo from "@/components/ui/Logo";
import { ProgressRing } from "@/components/ui/Progress";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { compact } from "@/lib/format";
import type { Chapter, Entity, Project } from "@/lib/types";
import EditorTab, { markChaptersScanned } from "./EditorTab";
import Organizer from "./Organizer";
import ExportTab from "./ExportTab";
import PlanTab from "./PlanTab";
import WorldBibleTab from "./WorldBibleTab";

const TABS = [
  { id: "plan", label: "Plan", icon: ListTree },
  { id: "write", label: "Write", icon: PenLine },
  { id: "world", label: "World Bible", icon: BookMarked },
  { id: "export", label: "Export", icon: Download },
] as const;
type TabId = (typeof TABS)[number]["id"];

export interface WorkspaceProps {
  initialProject: Project;
  initialChapters: Chapter[];
  initialEntities: Entity[];
  docxExport: boolean;
}

export default function Workspace({ initialProject, initialChapters, initialEntities, docxExport }: WorkspaceProps) {
  const [tab, setTab] = useState<TabId>(initialChapters.some((c) => c.word_count > 0) ? "write" : "plan");
  const [project, setProject] = useState(initialProject);
  useEffect(() => {
    document.title = `${project.title || "Untitled"} — MANTIS Studio`;
  }, [project.title]);
  const [chapters, setChapters] = useState(initialChapters);
  const [entities, setEntities] = useState(initialEntities);
  const [focus, setFocus] = useState(false);
  // Fresh import: organize the whole book automatically (World Bible, canon, summaries, plan, outline).
  const [organizing, setOrganizing] = useState(false);
  useEffect(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.get("organize") !== "1") return;
    url.searchParams.delete("organize");
    window.history.replaceState(null, "", url.pathname + url.search);
    markChaptersScanned(initialChapters);
    setOrganizing(true);
  }, [initialChapters]);

  const totalWords = useMemo(() => chapters.reduce((a, c) => a + (c.word_count || 0), 0), [chapters]);
  const target = project.target_words || 80000;
  const pct = (totalWords / target) * 100;

  const aiContext = useMemo(
    () => ({
      project: {
        title: project.title,
        genre: project.genre,
        premise: project.premise,
        outline: project.outline,
        canon_rules: project.canon_rules,
        style_guide: project.style_guide,
        style_dials: project.style_dials ?? null,
      },
      entities: entities.map((e) => ({ name: e.name, category: e.category, description: e.description, aliases: e.aliases })),
    }),
    [project, entities],
  );

  return (
    <div className="flex min-h-screen flex-col">
      <header className={`sticky top-0 z-20 border-b border-line bg-panel/90 backdrop-blur ${focus ? "hidden" : ""}`}>
        <div className="flex h-14 items-center gap-3 px-3 sm:px-5">
          <Link href="/app" className="btn-quiet h-9 w-9 p-0" aria-label="Back to projects" title="All projects">
            <ArrowLeft size={17} />
          </Link>
          <div className="hidden sm:block">
            <Logo href="/app" compact />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate font-serif text-base font-semibold sm:text-lg">{project.title || "Untitled"}</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right text-xs leading-tight text-muted sm:block">
              <p className="font-medium text-text">{compact(totalWords)} words</p>
              <p>of {compact(target)}</p>
            </div>
            <ProgressRing value={pct} size={38} />
            <ThemeToggle />
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 sm:px-5" aria-label="Project sections">
          {TABS.map((t) => {
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                aria-current={active ? "page" : undefined}
                className={`flex cursor-pointer items-center gap-2 border-b-2 px-3 py-2.5 text-sm whitespace-nowrap transition ${
                  active ? "border-accent font-medium text-text" : "border-transparent text-muted hover:text-text"
                }`}
              >
                <t.icon size={15} className={active ? "text-accent" : ""} />
                {t.label}
                {t.id === "world" && entities.length > 0 && <span className="text-xs text-muted">{entities.length}</span>}
              </button>
            );
          })}
        </nav>
      </header>
      {organizing && (
        <Organizer
          project={project}
          setProject={setProject}
          chapters={chapters}
          setChapters={setChapters}
          entities={entities}
          setEntities={setEntities}
          onClose={() => setOrganizing(false)}
        />
      )}
      <div className="flex-1">
        {tab === "plan" && (
          <PlanTab
            project={project}
            setProject={setProject}
            chapters={chapters}
            setChapters={setChapters}
            aiContext={aiContext}
            goToWrite={() => setTab("write")}
          />
        )}
        {tab === "write" && (
          <EditorTab
            project={project}
            chapters={chapters}
            setChapters={setChapters}
            entities={entities}
            setEntities={setEntities}
            setProject={setProject}
            aiContext={aiContext}
            focus={focus}
            setFocus={setFocus}
          />
        )}
        {tab === "world" && <WorldBibleTab project={project} setProject={setProject} chapters={chapters} setChapters={setChapters} entities={entities} setEntities={setEntities} />}
        {tab === "export" && <ExportTab project={project} chapters={chapters} docxExport={docxExport} />}
      </div>
    </div>
  );
}
