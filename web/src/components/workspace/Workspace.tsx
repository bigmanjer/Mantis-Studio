"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import type { Chapter, Entity, Project } from "@/lib/types";
import EditorTab from "./EditorTab";
import ExportTab from "./ExportTab";
import PlanTab from "./PlanTab";
import WorldBibleTab from "./WorldBibleTab";

const TABS = [
  ["plan", "Plan"],
  ["write", "Write"],
  ["world", "World Bible"],
  ["export", "Export"],
] as const;
type TabId = (typeof TABS)[number][0];

export interface WorkspaceProps {
  initialProject: Project;
  initialChapters: Chapter[];
  initialEntities: Entity[];
  docxExport: boolean;
}

export default function Workspace({ initialProject, initialChapters, initialEntities, docxExport }: WorkspaceProps) {
  const [tab, setTab] = useState<TabId>(initialChapters.some((c) => c.word_count > 0) ? "write" : "plan");
  const [project, setProject] = useState(initialProject);
  const [chapters, setChapters] = useState(initialChapters);
  const [entities, setEntities] = useState(initialEntities);

  const totalWords = useMemo(() => chapters.reduce((a, c) => a + (c.word_count || 0), 0), [chapters]);
  const pct = Math.min(100, Math.round((totalWords / (project.target_words || 80000)) * 100));

  const aiContext = useMemo(
    () => ({
      project: {
        title: project.title,
        genre: project.genre,
        premise: project.premise,
        outline: project.outline,
        canon_rules: project.canon_rules,
        style_guide: project.style_guide,
      },
      entities: entities.map((e) => ({ name: e.name, category: e.category, description: e.description })),
    }),
    [project, entities],
  );

  return (
    <div className="flex min-h-screen flex-col">
      <div className="border-b border-line bg-panel/50 px-4 pt-5">
        <div className="mx-auto max-w-6xl">
          <Link href="/app" className="text-xs text-muted hover:text-text">
            ← All projects
          </Link>
          <div className="mt-1 flex flex-wrap items-end justify-between gap-3">
            <h1 className="font-serif text-2xl font-semibold">{project.title}</h1>
            <div className="w-56 text-right text-xs text-muted">
              {totalWords.toLocaleString()} / {(project.target_words || 80000).toLocaleString()} words ({pct}%)
              <div className="mt-1 h-1.5 rounded-full bg-panel-2">
                <div className="h-1.5 rounded-full bg-accent" style={{ width: `${pct}%` }} />
              </div>
            </div>
          </div>
          <nav className="mt-4 flex gap-1 overflow-x-auto">
            {TABS.map(([id, label]) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`cursor-pointer border-b-2 px-4 py-2 text-sm whitespace-nowrap ${
                  tab === id ? "border-accent text-text" : "border-transparent text-muted hover:text-text"
                }`}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
      </div>
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
          <EditorTab project={project} chapters={chapters} setChapters={setChapters} entities={entities} setEntities={setEntities} aiContext={aiContext} />
        )}
        {tab === "world" && <WorldBibleTab project={project} entities={entities} setEntities={setEntities} />}
        {tab === "export" && <ExportTab project={project} chapters={chapters} docxExport={docxExport} />}
      </div>
    </div>
  );
}
