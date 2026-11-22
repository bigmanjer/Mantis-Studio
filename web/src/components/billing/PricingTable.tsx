"use client";
import { Check, Sparkles } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { PLANS, type Interval, type PlanId } from "@/lib/plans";
import UpgradeButton from "./UpgradeButton";

export default function PricingTable({ currentPlan, signedIn }: { currentPlan?: PlanId; signedIn: boolean }) {
  const [interval, setInterval] = useState<Interval>("year");
  const order: PlanId[] = ["free", "pro", "studio"];
  return (
    <>
      <div className="mb-10 flex justify-center">
        <div className="inline-flex rounded-full border border-line bg-panel p-1 text-sm shadow-soft" role="radiogroup" aria-label="Billing period">
          {(["month", "year"] as const).map((i) => (
            <button
              key={i}
              role="radio"
              aria-checked={interval === i}
              onClick={() => setInterval(i)}
              className={`cursor-pointer rounded-full px-4 py-1.5 transition ${interval === i ? "bg-accent text-accent-fg" : "text-muted hover:text-text"}`}
            >
              {i === "month" ? "Monthly" : (
                <>
                  Yearly <span className={interval === i ? "opacity-80" : "text-accent"}>· 2 months free</span>
                </>
              )}
            </button>
          ))}
        </div>
      </div>
      <div className="@container">
      <div className="grid items-stretch gap-6 @3xl:grid-cols-3">
        {order.map((id) => {
          const p = PLANS[id];
          const featured = id === "studio";
          const isCurrent = currentPlan === id;
          const cls = `${featured ? "btn-primary" : "btn-ghost"} w-full py-2.5`;
          const perMonth = interval === "year" ? p.yearly / 12 : p.monthly;
          return (
            <div
              key={id}
              className={`relative flex flex-col rounded-2xl border p-7 ${
                featured ? "border-accent/50 bg-panel shadow-glow" : "border-line bg-panel shadow-soft"
              }`}
            >
              {featured && (
                <span className="absolute -top-3 left-7 inline-flex items-center gap-1 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accent-fg">
                  <Sparkles size={12} /> Best value
                </span>
              )}
              <h3 className="text-lg font-semibold">{p.name}</h3>
              <p className="mt-1 min-h-10 text-sm text-muted">{p.tagline}</p>
              <div className="mt-6 flex items-baseline gap-1">
                <span className="font-serif text-5xl font-semibold tracking-tight">
                  ${Number.isInteger(perMonth) ? perMonth : perMonth.toFixed(2)}
                </span>
                <span className="text-sm text-muted">{id === "free" ? "forever" : "/ month"}</span>
              </div>
              <p className="mt-1 h-4 text-xs text-muted">
                {id !== "free" && interval === "year" ? `$${p.yearly} billed yearly` : id !== "free" ? "Billed monthly" : ""}
              </p>
              <div className="mt-6">
                {isCurrent ? (
                  <span className="btn-ghost w-full cursor-default py-2.5">Your current plan</span>
                ) : id === "free" ? (
                  <Link href={signedIn ? "/app" : "/signup"} className={cls}>
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
              <ul className="mt-7 flex-1 space-y-3 border-t border-line pt-6 text-sm">
                {p.features.map((f) => (
                  <li key={f} className="flex gap-2.5">
                    <Check size={16} className="mt-0.5 shrink-0 text-accent" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
      </div>
      <p className="mt-8 text-center text-xs text-muted">Prices in USD. Cancel any time from Settings. Taxes may apply.</p>
    </>
  );
}
