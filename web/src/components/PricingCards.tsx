"use client";
import Link from "next/link";
import { useState } from "react";
import { PLANS, type Interval, type PlanId } from "@/lib/plans";
import UpgradeButton from "./UpgradeButton";

export default function PricingCards({ currentPlan, signedIn }: { currentPlan?: PlanId; signedIn: boolean }) {
  const [interval, setInterval] = useState<Interval>("year");
  const order: PlanId[] = ["free", "pro", "studio"];
  return (
    <>
      <div className="mb-8 flex justify-center">
        <div className="inline-flex rounded-full border border-line bg-panel p-1 text-sm" role="radiogroup" aria-label="Billing period">
          {(["month", "year"] as const).map((i) => (
            <button
              key={i}
              role="radio"
              aria-checked={interval === i}
              onClick={() => setInterval(i)}
              className={`cursor-pointer rounded-full px-4 py-1.5 ${interval === i ? "bg-accent text-black" : "text-muted hover:text-text"}`}
            >
              {i === "month" ? "Monthly" : "Yearly — 2 months free"}
            </button>
          ))}
        </div>
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        {order.map((id) => {
          const p = PLANS[id];
          const highlight = id === "studio";
          const isCurrent = currentPlan === id;
          const cls = highlight ? "btn-primary w-full" : "btn-ghost w-full";
          const perMonth = interval === "year" ? p.yearly / 12 : p.monthly;
          return (
            <div
              key={id}
              className={`card flex flex-col p-6 ${highlight ? "border-accent/60 shadow-[0_0_50px_-20px_var(--accent)]" : ""}`}
            >
              <div className="flex h-7 items-start">
                {highlight && (
                  <span className="rounded-full bg-accent/15 px-3 py-1 text-xs font-medium text-accent">Best value</span>
                )}
              </div>
              <h3 className="mt-2 text-xl font-semibold">{p.name}</h3>
              <p className="mt-1 text-sm text-muted">{p.tagline}</p>
              <p className="mt-5 text-4xl font-bold">
                ${Number.isInteger(perMonth) ? perMonth : perMonth.toFixed(2)}
                <span className="text-base font-normal text-muted">{id === "free" ? " forever" : " / month"}</span>
              </p>
              <p className="mt-1 h-4 text-xs text-muted">{id !== "free" && interval === "year" ? `Billed $${p.yearly} yearly` : ""}</p>
              <ul className="mt-6 flex-1 space-y-2 text-sm">
                {p.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <span className="text-accent">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <div className="mt-8">
                {isCurrent ? (
                  <span className="btn-ghost w-full cursor-default">Current plan</span>
                ) : id === "free" ? (
                  <Link href={signedIn ? "/app" : "/signup"} className="btn-ghost w-full">
                    {signedIn ? "Open Studio" : "Start free"}
                  </Link>
                ) : signedIn ? (
                  <UpgradeButton plan={id} interval={interval} className={cls}>
                    {currentPlan && currentPlan !== "free" ? `Switch to ${p.name}` : `Upgrade to ${p.name}`}
                  </UpgradeButton>
                ) : (
                  <Link href={`/signup?plan=${id}&interval=${interval}`} className={cls}>
                    Get {p.name}
                  </Link>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-6 text-center text-xs text-muted">Cancel any time. Prices in USD. Taxes may apply.</p>
    </>
  );
}
