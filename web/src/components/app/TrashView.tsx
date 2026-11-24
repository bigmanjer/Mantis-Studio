"use client";
import { RotateCcw, Trash2 } from "lucide-react";
import { useState, useTransition } from "react";
import { purgeProject, restoreProject } from "@/app/app/actions";
import { useConfirm } from "@/components/ui/ConfirmDialog";
import EmptyState from "@/components/ui/EmptyState";

export interface TrashedBook {
  id: string;
  title: string;
  deleted_at: string;
  words: number;
  chapters: number;
}

const DAY = 86_400_000;

/** Books moved to the Trash, restorable for 30 days. */
export default function TrashView({ books: initial }: { books: TrashedBook[] }) {
  const confirm = useConfirm();
  const [books, setBooks] = useState(initial);
  const [err, setErr] = useState("");
  const [pending, start] = useTransition();
  const [busyId, setBusyId] = useState<string | null>(null);

  function restore(b: TrashedBook) {
    setErr("");
    setBusyId(b.id);
    start(async () => {
      const res = await restoreProject(b.id);
      if (res?.error) setErr(res.error);
      setBusyId(null);
    });
  }

  async function purge(b: TrashedBook) {
    const ok = await confirm({
      title: `Delete “${b.title || "Untitled"}” forever?`,
      body: `${b.words.toLocaleString()} words in ${b.chapters} ${b.chapters === 1 ? "chapter" : "chapters"}, plus its World Bible, will be permanently deleted. This can't be undone.`,
      confirmLabel: "Delete forever",
      danger: true,
    });
    if (!ok) return;
    setErr("");
    setBusyId(b.id);
    start(async () => {
      const res = await purgeProject(b.id);
      if (res?.error) setErr(res.error);
      else setBooks((list) => list.filter((x) => x.id !== b.id));
      setBusyId(null);
    });
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-8 sm:py-10">
      <h1 className="font-serif text-3xl font-semibold">Trash</h1>
      <p className="mt-1 text-sm text-muted">Books you delete wait here for 30 days. Restore one to bring back every chapter, note and World Bible entry.</p>
      {err && <p className="mt-4 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{err}</p>}

      {books.length === 0 ? (
        <div className="mt-8">
          <EmptyState icon={Trash2} title="The Trash is empty" body="Deleted books show up here, and you can restore them for 30 days." />
        </div>
      ) : (
        <ul className="mt-6 space-y-3">
          {books.map((b) => {
            const left = Math.max(0, 30 - Math.floor((Date.now() - new Date(b.deleted_at).getTime()) / DAY));
            return (
              <li key={b.id} className="card flex flex-wrap items-center gap-4 p-4">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-serif text-lg font-semibold">{b.title || "Untitled"}</p>
                  <p className="text-xs text-muted">
                    {b.words.toLocaleString()} words · {b.chapters} {b.chapters === 1 ? "chapter" : "chapters"} ·{" "}
                    <span className={left <= 3 ? "text-danger" : ""}>{left === 0 ? "deleted for good today" : `deleted for good in ${left} ${left === 1 ? "day" : "days"}`}</span>
                  </p>
                </div>
                <button onClick={() => restore(b)} disabled={pending} className="btn-primary">
                  <RotateCcw size={15} /> {busyId === b.id && pending ? "Restoring…" : "Restore"}
                </button>
                <button onClick={() => purge(b)} disabled={pending} className="btn-ghost text-danger" aria-label={`Delete ${b.title} forever`}>
                  <Trash2 size={15} /> Delete forever
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
