"use client";
import { FileUp, Loader2, Upload, X } from "lucide-react";
import { useRef, useState, useTransition } from "react";
import { importProject } from "@/app/app/actions";

/** "Import manuscript" button + dialog. Hidden when the plan's project limit is reached. */
export default function ImportDialog({ atLimit }: { atLimit: boolean }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [pending, start] = useTransition();

  if (atLimit) return null;

  const pick = (f: File | undefined | null) => {
    setError("");
    setFile(f ?? null);
  };

  return (
    <>
      <button
        onClick={() => {
          setError("");
          dialog.current?.showModal();
        }}
        className="btn-ghost"
      >
        <Upload size={15} /> Import
      </button>
      <dialog
        ref={dialog}
        className="m-auto w-[min(94vw,520px)] rounded-2xl border border-line bg-panel p-0 text-text shadow-soft backdrop:bg-black/60 backdrop:backdrop-blur-sm"
      >
        <form
          action={(fd) =>
            start(async () => {
              if (!file) return setError("Choose a file to import.");
              fd.set("file", file);
              const res = await importProject(fd);
              if (res?.error) setError(res.error);
            })
          }
          className="p-6"
        >
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-serif text-2xl font-semibold">Import a manuscript</h2>
              <p className="mt-1 text-sm text-muted">We&apos;ll split it into chapters using its headings (Chapter 1, Prologue, # Heading…).</p>
            </div>
            <button type="button" onClick={() => dialog.current?.close()} className="btn-quiet h-8 w-8 p-0" aria-label="Close">
              <X size={16} />
            </button>
          </div>

          <label
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              pick(e.dataTransfer.files?.[0]);
            }}
            className={`mt-6 flex cursor-pointer flex-col items-center gap-2 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition ${
              dragging ? "border-accent bg-accent-soft" : "border-line-strong hover:border-accent/60"
            }`}
          >
            <FileUp size={26} className="text-accent" />
            {file ? (
              <>
                <span className="font-medium">{file.name}</span>
                <span className="text-xs text-muted">{(file.size / 1024).toFixed(0)} KB · click to choose another</span>
              </>
            ) : (
              <>
                <span className="font-medium">Drop a file here, or click to browse</span>
                <span className="text-xs text-muted">Word (.docx), Markdown (.md) or text (.txt), up to 6 MB</span>
              </>
            )}
            <input type="file" accept=".docx,.md,.markdown,.txt" className="sr-only" onChange={(e) => pick(e.target.files?.[0])} />
          </label>

          <div className="mt-4">
            <label className="label" htmlFor="imp-title">
              Title <span className="normal-case">(optional, defaults to the file name)</span>
            </label>
            <input id="imp-title" name="title" className="input" placeholder="The Glass Orchard" />
          </div>

          {error && <p className="mt-4 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>}
          <div className="mt-6 flex justify-end gap-2">
            <button type="button" onClick={() => dialog.current?.close()} className="btn-ghost">
              Cancel
            </button>
            <button type="submit" disabled={pending || !file} className="btn-primary">
              {pending ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />}
              {pending ? "Importing…" : "Import"}
            </button>
          </div>
        </form>
      </dialog>
    </>
  );
}
