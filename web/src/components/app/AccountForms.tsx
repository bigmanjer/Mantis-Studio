"use client";
import { useState, useTransition } from "react";
import { deleteAccount } from "@/app/app/actions";
import { createClient } from "@/lib/supabase/client";

export function ChangePasswordForm({ highlight }: { highlight: boolean }) {
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (pw.length < 8) return setMsg({ ok: false, text: "Use at least 8 characters." });
    if (pw !== pw2) return setMsg({ ok: false, text: "Passwords don't match." });
    setBusy(true);
    const { error } = await createClient().auth.updateUser({ password: pw });
    setBusy(false);
    setMsg(error ? { ok: false, text: error.message } : { ok: true, text: "Password updated." });
    if (!error) {
      setPw("");
      setPw2("");
    }
  }

  return (
    <form onSubmit={submit} className={`card p-6 ${highlight ? "border-accent/60" : ""}`}>
      <h2 className="text-lg font-semibold">{highlight ? "Set a new password" : "Change password"}</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <input type="password" autoComplete="new-password" className="input" placeholder="New password" value={pw} onChange={(e) => setPw(e.target.value)} />
        <input type="password" autoComplete="new-password" className="input" placeholder="Confirm new password" value={pw2} onChange={(e) => setPw2(e.target.value)} />
      </div>
      <div className="mt-4 flex items-center gap-3">
        <button disabled={busy} className="btn-primary">
          {busy ? "Saving…" : "Update password"}
        </button>
        {msg && <span className={`text-sm ${msg.ok ? "text-accent" : "text-danger"}`}>{msg.text}</span>}
      </div>
    </form>
  );
}

export function DeleteAccountForm({ email }: { email: string }) {
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [err, setErr] = useState("");
  const [pending, start] = useTransition();

  return (
    <section className="card border-danger/30 p-6">
      <h2 className="text-lg font-semibold text-danger">Delete account</h2>
      <p className="mt-1 text-sm text-muted">
        Permanently deletes your account, every project, chapter and World Bible entry, and cancels any subscription. This can&apos;t be
        undone. Export anything you want to keep first.
      </p>
      {!open ? (
        <button onClick={() => setOpen(true)} className="btn-danger mt-4">
          Delete my account…
        </button>
      ) : (
        <div className="mt-4 space-y-3">
          <label className="text-sm" htmlFor="confirm-email">
            Type <span className="font-mono text-text">{email}</span> to confirm:
          </label>
          <input id="confirm-email" className="input" value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off" />
          {err && <p className="text-sm text-danger">{err}</p>}
          <div className="flex gap-2">
            <button
              disabled={pending || typed.trim().toLowerCase() !== email.toLowerCase()}
              onClick={() =>
                start(async () => {
                  setErr("");
                  const res = await deleteAccount(typed);
                  if (res?.error) setErr(res.error);
                })
              }
              className="btn-danger"
            >
              {pending ? "Deleting…" : "Permanently delete"}
            </button>
            <button onClick={() => setOpen(false)} className="btn-ghost">
              Cancel
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
