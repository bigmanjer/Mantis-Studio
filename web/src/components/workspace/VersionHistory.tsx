"use client";
import { History, Loader2, RotateCcw, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { timeAgo } from "@/lib/format";

export interface ChapterVersion {
  id: string;
  title: string;
  content: string;
  word_count: number;
  reason: string;
  created_at: string;
}

/** "History" button + dialog listing saved versions of a chapter, with preview and restore. */
export default function VersionHistory({
  chapterId,
  onRestore,
}: {
  chapterId: string;
  onRestore: (v: ChapterVersion) => Promise<void> | void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [versions, setVersions] = useState<ChapterVersion[] | null>(null);
  const [selected, setSelected] = useState<ChapterVersion | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    createClient()
      .from("chapter_versions")
      .select("id, title, content, word_count, reason, created_at")
      .eq("chapter_id", chapterId)
      .order("created_at", { ascending: false })
      .limit(50)
      .then(({ data }) => {
        if (cancelled) return;
        const list = (data ?? []) as ChapterVersion[];
        setVersions(list);
        setSelected(list[0] ?? null);
      });
    return () => {
      cancelled = true;
    };
  }, [open, chapterId]);

  const show = () => {
    setVersions(null);
    setOpen(true);
    dialog.current?.showModal();
  };
  const close = () => {
    setOpen(false);
    dialog.current?.close();
  };

  return (
    <>
      <button onClick={show} className="flex cursor-pointer items-center gap-1.5 hover:text-text" title="See and restore earlier versions">
        <History size={13} /> History
      </button>
      <dialog
        ref={dialog}
        onClose={() => setOpen(false)}
        className="m-auto h-[min(86vh,720px)] w-[min(96vw,980px)] rounded-2xl border border-line bg-panel p-0 text-text shadow-soft backdrop:bg-black/60 backdrop:backdrop-blur-sm"
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b border-line px-5 py-3">
            <div>
              <h2 className="font-semibold">Version history</h2>
              <p className="text-xs text-muted">Saved automatically while you write, and before every AI edit. Newest first.</p>
            </div>
            <button onClick={close} className="btn-quiet h-8 w-8 p-0" aria-label="Close">
              <X size={16} />
            </button>
          </div>
          {versions === null ? (
            <div className="flex flex-1 items-center justify-center text-muted">
              <Loader2 size={18} className="animate-spin" />
            </div>
          ) : versions.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-2 p-10 text-center text-sm text-muted">
              <History size={22} className="text-accent" />
              No saved versions yet. They appear as you write (every 10 minutes) and before AI edits.
            </div>
          ) : (
            <div className="grid min-h-0 flex-1 sm:grid-cols-[240px_1fr]">
              <ul className="max-h-48 overflow-y-auto border-b border-line p-2 sm:max-h-none sm:border-r sm:border-b-0">
                {versions.map((v) => (
                  <li key={v.id}>
                    <button
                      onClick={() => setSelected(v)}
                      className={`w-full cursor-pointer rounded-lg px-3 py-2 text-left transition ${
                        selected?.id === v.id ? "bg-panel-3" : "hover:bg-panel-2"
                      }`}
                    >
                      <p className="text-sm">{timeAgo(v.created_at)}</p>
                      <p className="text-[11px] text-muted">
                        {v.reason} · {v.word_count.toLocaleString()} words
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
              <div className="flex min-h-0 flex-col">
                <div className="flex-1 overflow-y-auto bg-paper px-6 py-5">
                  <p className="font-serif text-lg font-semibold">{selected?.title}</p>
                  <p className="prose-editor mt-3 text-[15px] whitespace-pre-wrap">{selected?.content || "(empty)"}</p>
                </div>
                <div className="flex items-center justify-between gap-3 border-t border-line px-5 py-3">
                  <p className="text-xs text-muted">Restoring keeps a copy of what you have now, so nothing is lost.</p>
                  <button
                    disabled={!selected || restoring}
                    onClick={async () => {
                      if (!selected) return;
                      setRestoring(true);
                      await onRestore(selected);
                      setRestoring(false);
                      close();
                    }}
                    className="btn-primary"
                  >
                    {restoring ? <Loader2 size={15} className="animate-spin" /> : <RotateCcw size={15} />}
                    Restore this version
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </dialog>
    </>
  );
}
