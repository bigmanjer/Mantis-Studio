"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "error" | "info"; text: string } | null>(null);

  const rawPlan = params.get("plan");
  const plan = rawPlan === "pro" || rawPlan === "studio" ? rawPlan : null;
  const interval = params.get("interval") === "month" ? "month" : "year";
  const rawNext = params.get("next");
  // Only allow same-site relative paths, so a crafted link can't bounce users to another site.
  const safeNext = rawNext && rawNext.startsWith("/") && !rawNext.startsWith("//") && !rawNext.includes("\\") ? rawNext : null;
  const next = safeNext || (plan ? `/app/settings?upgrade=${plan}&interval=${interval}` : "/app");
  const notConfigured = params.get("setup") === "1";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    const supabase = createClient();
    if (mode === "signup") {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { emailRedirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}` },
      });
      if (error) setMsg({ kind: "error", text: error.message });
      else if (!data.session) setMsg({ kind: "info", text: "Check your email to confirm your account, then log in." });
      else {
        router.push(next);
        router.refresh();
      }
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) setMsg({ kind: "error", text: error.message });
      else {
        router.push(next);
        router.refresh();
      }
    }
    setBusy(false);
  }

  async function resetPassword() {
    if (!email) {
      setMsg({ kind: "error", text: "Enter your email first, then click \"Forgot password\"." });
      return;
    }
    const supabase = createClient();
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/callback?next=/app/settings%3Freset%3D1`,
    });
    setMsg(error ? { kind: "error", text: error.message } : { kind: "info", text: "Password reset email sent." });
  }

  return (
    <div className="w-full max-w-sm">
      <h1 className="font-serif text-3xl font-semibold">{mode === "login" ? "Welcome back" : "Start your book"}</h1>
      <p className="mt-2 text-sm text-muted">
        {mode === "login"
          ? "Log in to pick up where you left off."
          : plan
            ? `Create your account, then finish upgrading to ${plan === "studio" ? "Studio" : "Pro"}.`
            : "Free forever plan. No credit card needed."}
      </p>
      {notConfigured && (
        <p className="mt-4 rounded-lg border border-danger/30 bg-danger-soft p-3 text-xs text-danger">
          Accounts aren&apos;t configured on this server yet (missing Supabase settings).
        </p>
      )}
      <form onSubmit={submit} className="mt-6 space-y-4">
        <div>
          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            className="input py-2.5"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <div className="flex items-center justify-between">
            <label className="label" htmlFor="password">
              Password
            </label>
            {mode === "login" && (
              <button type="button" onClick={resetPassword} className="mb-1.5 cursor-pointer text-xs text-muted hover:text-text">
                Forgot password?
              </button>
            )}
          </div>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            className="input py-2.5"
            placeholder={mode === "signup" ? "At least 8 characters" : ""}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {msg && (
          <p
            role="status"
            className={`rounded-lg border px-3 py-2 text-sm ${msg.kind === "error" ? "border-danger/30 bg-danger-soft text-danger" : "border-accent/30 bg-accent-soft text-accent"}`}
          >
            {msg.text}
          </p>
        )}
        <button type="submit" disabled={busy} className="btn-primary w-full py-2.5">
          {busy ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
        </button>
      </form>
      <p className="mt-8 text-center text-sm text-muted">
        {mode === "login" ? "New to MANTIS? " : "Already have an account? "}
        <Link
          href={`/${mode === "login" ? "signup" : "login"}${plan ? `?plan=${plan}&interval=${interval}` : ""}`}
          className="font-medium text-accent hover:underline"
        >
          {mode === "login" ? "Create a free account" : "Log in"}
        </Link>
      </p>
    </div>
  );
}
