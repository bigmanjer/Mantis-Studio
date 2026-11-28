"use client";
import { ArrowLeft, BookMarked, Download, Gauge, Image as ImageIcon, Library, ListTree, PenLine } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import Logo from "@/components/ui/Logo";
import { ProgressRing } from "@/components/ui/Progress";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { compact } from "@/lib/format";
import type { Chapter, Entity, EntityLink, Project } from "@/lib/types";
import EditorTab, { markChaptersScanned } from "./EditorTab";
import Organizer from "./Organizer";
import ArtTab from "./ArtTab";
import ExportTab from "./ExportTab";
import InsightsTab from "./InsightsTab";
import KnowledgeTab from "./KnowledgeTab";
import PlanTab from "./PlanTab";
import WorldBibleTab from "./WorldBibleTab";

const TABS = [
  { id: "plan", label: "Plan", icon: ListTree },
  { id: "write", label: "Write", icon: PenLine },
  { id: "world", label: "World Bible", icon: BookMarked },
  { id: "insights", label: "Insights", icon: Gauge },
  { id: "library", label: "Library", icon: Library },
  { id: "art", label: "Art", icon: ImageIcon },
  { id: "export", label: "Export", icon: Download },
] as const;
type TabId = (typeof TABS)[number]["id"];

export interface WorkspaceProps {
  initialProject: Project;
  initialChapters: Chapter[];
  initialEntities: Entity[];
  initialLinks: EntityLink[];
  docxExport: boolean;
  /** Paid plan, admin, or own AI key: automatic World Bible and fixes may run. */
  autoAllowed: boolean;
  /** Book art: on, off, or "setup" (admin sees how to switch it on). */
  art: "on" | "off" | "setup";
}

export default function Workspace({ initialProject, initialChapters, initialEntities, initialLinks, docxExport, autoAllowed, art }: WorkspaceProps) {
  const [tab, setTab] = useState<TabId>(initialChapters.some((c) => c.word_count > 0) ? "write" : "plan");
  const [project, setProject] = useState(initialProject);
  useEffect(() => {
    document.title = `${project.title || "Untitled"} — MANTIS Studio`;
  }, [project.title]);
  const [chapters, setChapters] = useState(initialChapters);
  const [entities, setEntities] = useState(initialEntities);
  const [links, setLinks] = useState(initialLinks);
  const [focus, setFocus] = useState(false);
  // Fresh import: organize the whole book automatically (World Bible, canon, summaries, plan, outline).
  const [organizing, setOrganizing] = useState(false);
  const [organizeLimit, setOrganizeLimit] = useState(false);
  useEffect(() => {
    const url = new URL(window.location.href);
    const organize = url.searchParams.get("organize");
    if (organize !== "1" && organize !== "limit") return;
    url.searchParams.delete("organize");
    window.history.replaceState(null, "", url.pathname + url.search);
    markChaptersScanned(initialChapters);
    if (organize === "limit") setOrganizeLimit(true);
    else setOrganizing(true);
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
        id: project.id,
        use_knowledge: project.use_knowledge !== false,
        style_lenses: project.style_lenses ?? [],
      },
      entities: entities.map((e) => ({ name: e.name, category: e.category, description: e.description, aliases: e.aliases })),
      // Relationships the writer drew, so the AI knows who is whose brother, rival or mentor.
      relationships: links
        .map((l) => {
          const a = entities.find((e) => e.id === l.source_id);
          const b = entities.find((e) => e.id === l.target_id);
          return a && b ? `${a.name} → ${l.kind} → ${b.name}${l.note ? ` (${l.note})` : ""}` : "";
        })
        .filter(Boolean),
    }),
    [project, entities, links],
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
      {organizeLimit && (
        <div className="border-b border-line bg-panel px-4 py-3 text-sm sm:px-6" role="status">
          <div className="mx-auto flex max-w-6xl items-start justify-between gap-3">
            <p className="text-muted">
              <span className="font-medium text-text">Imported and split into {chapters.length} {chapters.length === 1 ? "chapter" : "chapters"}.</span> Automatic organizing
              (World Bible, outline, summaries) is included once on Free.{" "}
              <a href="/app/settings#ai" className="text-accent hover:underline">
                Add a free Groq key
              </a>{" "}
              or{" "}
              <a href="/app/settings#billing" className="text-accent hover:underline">
                upgrade
              </a>{" "}
              to organize every book, or use “Scan all chapters” in the World Bible.
            </p>
            <button onClick={() => setOrganizeLimit(false)} className="btn-quiet h-7 w-7 shrink-0 p-0" aria-label="Dismiss">
              ×
            </button>
          </div>
        </div>
      )}
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
            autoAllowed={autoAllowed}
            focus={focus}
            setFocus={setFocus}
          />
        )}
        {tab === "world" && <WorldBibleTab project={project} setProject={setProject} chapters={chapters} setChapters={setChapters} entities={entities} setEntities={setEntities} links={links} setLinks={setLinks} />}
        {tab === "insights" && <InsightsTab project={project} chapters={chapters} entities={entities} aiContext={aiContext} goTo={(t) => setTab(t)} />}
        {tab === "art" && <ArtTab project={project} setProject={setProject} chapters={chapters} aiContext={aiContext} art={art} />}
        {tab === "library" && <KnowledgeTab project={project} setProject={setProject} />}
        {tab === "export" && <ExportTab project={project} chapters={chapters} docxExport={docxExport} />}
      </div>
    </div>
  );
}
