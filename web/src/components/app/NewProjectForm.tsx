"use client";
import { Lock, Plus, X } from "lucide-react";
import Link from "next/link";
import { useRef, useState, useTransition } from "react";
import { createProject } from "@/app/app/actions";

const GENRES = ["Fantasy", "Science fiction", "Thriller", "Mystery", "Romance", "Literary", "Horror", "Historical", "Young adult"];

/** "New project" trigger. Renders a button (or a dashed tile) that opens the create dialog. */
export default function NewProjectForm({ atLimit, planName, variant = "button" }: { atLimit: boolean; planName: string; variant?: "button" | "tile" }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [error, setError] = useState("");
  const [pending, start] = useTransition();

  if (atLimit) {
    return variant === "tile" ? (
      <Link
        href="/app/settings#billing"
        className="flex min-h-56 flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-line-strong p-6 text-center text-sm text-muted transition hover:border-accent/50 hover:text-text"
      >
        <Lock size={20} />
        <span>
          {planName} includes 2 projects.
          <br />
          <span className="font-medium text-accent">Upgrade for unlimited</span>
        </span>
      </Link>
    ) : (
      <Link href="/app/settings#billing" className="btn-ghost">
        <Lock size={15} /> Upgrade for more projects
      </Link>
    );
  }

  const open = () => {
    setError("");
    dialog.current?.showModal();
  };

  return (
    <>
      {variant === "tile" ? (
        <button
          onClick={open}
          className="flex min-h-56 cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-line-strong p-6 text-sm text-muted transition hover:border-accent/60 hover:bg-accent-soft hover:text-text"
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-panel-3">
            <Plus size={18} />
          </span>
          New project
        </button>
      ) : (
        <button onClick={open} className="btn-primary">
          <Plus size={16} /> New project
        </button>
      )}

      <dialog
        ref={dialog}
        className="m-auto w-[min(94vw,520px)] rounded-2xl border border-line bg-panel p-0 text-text shadow-soft backdrop:bg-black/60 backdrop:backdrop-blur-sm"
      >
        <form
          action={(fd) =>
            start(async () => {
              setError("");
              const res = await createProject(fd);
              if (res?.error) setError(res.error);
            })
          }
          className="p-6"
        >
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-serif text-2xl font-semibold">Start a new book</h2>
              <p className="mt-1 text-sm text-muted">You can change all of this later.</p>
            </div>
            <button type="button" onClick={() => dialog.current?.close()} className="btn-quiet h-8 w-8 p-0" aria-label="Close">
              <X size={16} />
            </button>
          </div>
          <div className="mt-6 space-y-4">
            <div>
              <label className="label" htmlFor="np-title">
                Working title
              </label>
              <input id="np-title" name="title" className="input py-2.5" placeholder="The Glass Orchard" autoFocus />
            </div>
            <div>
              <label className="label" htmlFor="np-genre">
                Genre
              </label>
              <input id="np-genre" name="genre" list="np-genres" className="input py-2.5" placeholder="Pick or type a genre" />
              <datalist id="np-genres">
                {GENRES.map((g) => (
                  <option key={g} value={g} />
                ))}
              </datalist>
            </div>
            <div>
              <label className="label" htmlFor="np-premise">
                Premise <span className="normal-case">(optional)</span>
              </label>
              <textarea
                id="np-premise"
                name="premise"
                rows={4}
                className="input"
                placeholder="Who is the story about, what do they want, and what stands in the way?"
              />
            </div>
          </div>
          {error && <p className="mt-4 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>}
          <div className="mt-6 flex justify-end gap-2">
            <button type="button" onClick={() => dialog.current?.close()} className="btn-ghost">
              Cancel
            </button>
            <button type="submit" disabled={pending} className="btn-primary">
              {pending ? "Creating…" : "Create project"}
            </button>
          </div>
        </form>
      </dialog>
    </>
  );
}
