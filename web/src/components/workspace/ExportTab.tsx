"use client";
import { BookOpen, DatabaseBackup, FileDown, FileText, FileType2, Lock } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import type { Chapter, Project } from "@/lib/types";

export default function ExportTab({ project, chapters, docxExport }: { project: Project; chapters: Chapter[]; docxExport: boolean }) {
  const [includeOutline, setIncludeOutline] = useState(false);
  const words = chapters.reduce((a, c) => a + c.word_count, 0);
  const href = (format: string) => `/api/export/${project.id}?format=${format}${includeOutline ? "&outline=1" : ""}`;

  const FORMATS = [
    { id: "docx", icon: FileType2, title: "Word manuscript", ext: ".docx", body: "Standard manuscript format: Times New Roman, double-spaced, each chapter on a new page.", locked: !docxExport },
    {
      id: "epub",
      icon: BookOpen,
      title: "Ebook",
      ext: ".epub",
      body: "Ready for Kindle (KDP), Apple Books, Kobo and Google Play, with a title page and table of contents.",
      locked: !docxExport,
    },
    { id: "md", icon: FileText, title: "Markdown", ext: ".md", body: "Clean text with headings. Great for Scrivener, Obsidian, Vellum or GitHub." },
    { id: "txt", icon: FileDown, title: "Plain text", ext: ".txt", body: "Just the words. Opens anywhere." },
    {
      id: "json",
      icon: DatabaseBackup,
      title: "Full backup",
      ext: ".json",
      body: "Everything: chapters, outline, canon rules, style and World Bible. Re-import it any time from Projects.",
    },
  ];

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <h1 className="font-serif text-2xl font-semibold">Export</h1>
      <p className="mt-1 text-sm text-muted">
        {chapters.length} chapter{chapters.length === 1 ? "" : "s"} · {words.toLocaleString()} words, in the order shown in the Write tab.
      </p>

      <label className="mt-6 flex w-fit cursor-pointer items-center gap-3 rounded-xl border border-line bg-panel px-4 py-3 text-sm">
        <input type="checkbox" className="h-4 w-4 accent-[var(--accent)]" checked={includeOutline} onChange={(e) => setIncludeOutline(e.target.checked)} />
        Include the premise and outline at the start
      </label>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {FORMATS.map((f) =>
          f.locked ? (
            <Link key={f.id} href="/app/settings#billing" className="card group flex flex-col p-5 opacity-80 transition hover:opacity-100">
              <div className="flex items-center justify-between">
                <f.icon size={22} className="text-muted" />
                <span className="flex items-center gap-1 rounded-full bg-panel-3 px-2 py-0.5 text-[11px] text-muted">
                  <Lock size={11} /> Pro
                </span>
              </div>
              <p className="mt-4 font-semibold">
                {f.title} <span className="text-xs font-normal text-muted">{f.ext}</span>
              </p>
              <p className="mt-1 flex-1 text-sm text-muted">{f.body}</p>
              <span className="mt-4 text-sm font-medium text-accent group-hover:underline">Upgrade to unlock</span>
            </Link>
          ) : (
            <a key={f.id} href={href(f.id)} className="card group flex flex-col p-5 transition hover:border-accent/50">
              <f.icon size={22} className="text-accent" />
              <p className="mt-4 font-semibold">
                {f.title} <span className="text-xs font-normal text-muted">{f.ext}</span>
              </p>
              <p className="mt-1 flex-1 text-sm text-muted">{f.body}</p>
              <span className="mt-4 text-sm font-medium text-accent group-hover:underline">Download</span>
            </a>
          ),
        )}
      </div>
    </div>
  );
}
