"use client";
import Link from "next/link";
import { useState, useTransition } from "react";
import { createProject } from "@/app/app/actions";

export default function NewProjectForm({ atLimit, planName }: { atLimit: boolean; planName: string }) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [pending, start] = useTransition();

  if (atLimit) {
    return (
      <div className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
        <p className="text-muted">You&apos;ve reached the project limit on the {planName} plan.</p>
        <Link href="/app/settings#plans" className="btn-primary">
          Upgrade for unlimited projects
        </Link>
      </div>
    );
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="btn-primary">
        + New project
      </button>
    );
  }

  return (
    <form
      action={(fd) =>
        start(async () => {
          setError("");
          const res = await createProject(fd);
          if (res?.error) setError(res.error);
        })
      }
      className="card space-y-4 p-5"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor="title">
            Title
          </label>
          <input id="title" name="title" className="input" placeholder="The Glass Orchard" autoFocus />
        </div>
        <div>
          <label className="label" htmlFor="genre">
            Genre
          </label>
          <input id="genre" name="genre" className="input" placeholder="Fantasy, thriller, romance…" />
        </div>
      </div>
      <div>
        <label className="label" htmlFor="premise">
          Premise (optional)
        </label>
        <textarea
          id="premise"
          name="premise"
          rows={3}
          className="input"
          placeholder="A one-paragraph pitch: who, what they want, and what stands in the way."
        />
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={pending} className="btn-primary">
          {pending ? "Creating…" : "Create project"}
        </button>
        <button type="button" onClick={() => setOpen(false)} className="btn-ghost">
          Cancel
        </button>
      </div>
    </form>
  );
}
