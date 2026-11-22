"use client";
import { useState } from "react";
import type { Interval, PlanId } from "@/lib/plans";

export default function UpgradeButton({
  plan,
  interval = "month",
  className,
  children,
}: {
  plan: PlanId;
  interval?: Interval;
  className?: string;
  children: React.ReactNode;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function go() {
    setBusy(true);
    setErr("");
    const res = await fetch("/api/stripe/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan, interval }),
    });
    const data = await res.json().catch(() => ({}));
    if (data.url) {
      window.location.href = data.url;
    } else {
      setErr(data.error ?? "Could not start checkout.");
      setBusy(false);
    }
  }

  return (
    <>
      <button onClick={go} disabled={busy} className={className}>
        {busy ? "Redirecting…" : children}
      </button>
      {err && <p className="mt-2 text-xs text-danger">{err}</p>}
    </>
  );
}
