"use client";
import Link from "next/link";
import { useState } from "react";
import type { Chapter, Project } from "@/lib/types";

export default function ExportTab({ project, chapters, docxExport }: { project: Project; chapters: Chapter[]; docxExport: boolean }) {
  const [includeOutline, setIncludeOutline] = useState(false);
  const words = chapters.reduce((a, c) => a + c.word_count, 0);
  const href = (format: string) => `/api/export/${project.id}?format=${format}${includeOutline ? "&outline=1" : ""}`;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="card p-6">
        <h2 className="text-lg font-semibold">Export manuscript</h2>
        <p className="mt-1 text-sm text-muted">
          {chapters.length} chapters · {words.toLocaleString()} words. Chapters are exported in the order shown in the Write tab.
        </p>
        <label className="mt-4 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={includeOutline} onChange={(e) => setIncludeOutline(e.target.checked)} />
          Include premise and outline at the start
        </label>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <a href={href("md")} className="btn-ghost">
            Markdown (.md)
          </a>
          <a href={href("txt")} className="btn-ghost">
            Plain text (.txt)
          </a>
          {docxExport ? (
            <a href={href("docx")} className="btn-primary">
              Word (.docx)
            </a>
          ) : (
            <Link href="/app/settings#plans" className="btn-ghost text-muted" title="Available on Pro and Studio">
              Word (.docx) 🔒
            </Link>
          )}
        </div>
        {!docxExport && (
          <p className="mt-3 text-xs text-muted">
            Word export with manuscript formatting is included with Pro and Studio.{" "}
            <Link href="/app/settings#plans" className="text-accent underline">
              Upgrade
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
