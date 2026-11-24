"use client";
import { diffWordsWithSpace } from "diff";
import { useMemo } from "react";

/**
 * Word-level "what changed" view for AI rewrites (the original MANTIS "Diff view"):
 * removed words struck through in red, added words highlighted in green.
 */
export default function ChangesView({ before, after, className = "" }: { before: string; after: string; className?: string }) {
  const parts = useMemo(() => diffWordsWithSpace(before, after), [before, after]);
  const stats = useMemo(() => {
    const count = (s: string) => s.split(/\s+/).filter(Boolean).length;
    return {
      added: parts.filter((p) => p.added).reduce((a, p) => a + count(p.value), 0),
      removed: parts.filter((p) => p.removed).reduce((a, p) => a + count(p.value), 0),
    };
  }, [parts]);

  return (
    <div className={className}>
      <p className="mb-2 text-[11px] text-muted">
        <span className="text-accent">+{stats.added.toLocaleString()} words</span> · <span className="text-danger">−{stats.removed.toLocaleString()} words</span>
      </p>
      <div className="font-serif text-[14px] leading-relaxed whitespace-pre-wrap">
        {parts.map((p, i) =>
          p.added ? (
            <ins key={i} className="rounded-sm bg-accent-soft text-accent no-underline">
              {p.value}
            </ins>
          ) : p.removed ? (
            <del key={i} className="rounded-sm bg-danger-soft text-danger/90 decoration-danger/60">
              {p.value}
            </del>
          ) : (
            <span key={i}>{p.value}</span>
          ),
        )}
      </div>
    </div>
  );
}
