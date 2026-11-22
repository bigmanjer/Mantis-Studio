import { CheckCircle2, CreditCard, KeyRound, Sparkles, UserRound, XCircle } from "lucide-react";
import PricingTable from "@/components/billing/PricingTable";
import UpgradeButton from "@/components/billing/UpgradeButton";
import Badge from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/Progress";
import type { Interval, Plan, PlanId } from "@/lib/plans";
import { ChangePasswordForm, DeleteAccountForm } from "./AccountForms";
import AiKeyForm from "./AiKeyForm";

export interface SettingsData {
  email: string;
  plan: Plan;
  subscriptionStatus: string | null;
  periodEnd: string | null;
  hasBillingAccount: boolean;
  aiUsed: number;
  aiProvider: string;
  aiModel: string;
  maskedKey: string | null;
}

const SECTIONS = [
  { id: "billing", label: "Plan & billing", icon: CreditCard },
  { id: "ai", label: "AI", icon: Sparkles },
  { id: "account", label: "Account", icon: UserRound },
];

function Section({ id, title, description, children }: { id: string; title: string; description: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-20 border-b border-line pb-12 last:border-0">
      <h2 className="text-xl font-semibold">{title}</h2>
      <p className="mt-1 text-sm text-muted">{description}</p>
      <div className="mt-6 space-y-6">{children}</div>
    </section>
  );
}

export default function SettingsView({
  data,
  flash,
}: {
  data: SettingsData;
  flash: { checkout?: string; upgrade?: PlanId; interval?: Interval; reset?: boolean };
}) {
  const { plan } = data;
  const pct = plan.includedAiTokens ? (data.aiUsed / plan.includedAiTokens) * 100 : 0;
  const paid = plan.id !== "free";

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
      <h1 className="font-serif text-3xl font-semibold sm:text-4xl">Settings</h1>

      <div className="mt-6 space-y-3">
        {flash.checkout === "success" && (
          <p className="flex items-center gap-2 rounded-xl border border-accent/30 bg-accent-soft px-4 py-3 text-sm text-accent">
            <CheckCircle2 size={16} /> Thanks for subscribing! Your plan updates within a few seconds; refresh if it still shows the old one.
          </p>
        )}
        {flash.checkout === "canceled" && (
          <p className="flex items-center gap-2 rounded-xl border border-line bg-panel px-4 py-3 text-sm text-muted">
            <XCircle size={16} /> Checkout canceled. You haven&apos;t been charged.
          </p>
        )}
        {flash.upgrade && plan.id === "free" && (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-accent/40 bg-accent-soft px-4 py-3">
            <p className="text-sm">
              One more step: finish upgrading to <strong>{flash.upgrade === "studio" ? "Studio" : "Pro"}</strong>.
            </p>
            <UpgradeButton plan={flash.upgrade} interval={flash.interval ?? "year"} className="btn-primary">
              Continue to checkout
            </UpgradeButton>
          </div>
        )}
        {flash.reset && <ChangePasswordForm highlight />}
      </div>

      <div className="mt-8 grid gap-10 lg:grid-cols-[200px_1fr]">
        <nav className="hidden lg:block" aria-label="Settings sections">
          <ul className="sticky top-8 space-y-0.5">
            {SECTIONS.map((s) => (
              <li key={s.id}>
                <a href={`#${s.id}`} className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted transition hover:bg-panel-2 hover:text-text">
                  <s.icon size={15} /> {s.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="min-w-0 space-y-12">
          <Section id="billing" title="Plan & billing" description="Your subscription, invoices and monthly AI allowance.">
            <div className="card grid gap-6 p-6 md:grid-cols-2">
              <div>
                <p className="label">Current plan</p>
                <div className="flex items-center gap-3">
                  <p className="font-serif text-3xl font-semibold">{plan.name}</p>
                  {paid && data.subscriptionStatus && (
                    <Badge tone={data.subscriptionStatus === "active" || data.subscriptionStatus === "trialing" ? "accent" : "danger"}>
                      {data.subscriptionStatus.replace("_", " ")}
                    </Badge>
                  )}
                </div>
                <p className="mt-1 text-sm text-muted">
                  {paid && data.periodEnd ? `Renews ${new Date(data.periodEnd).toLocaleDateString(undefined, { dateStyle: "medium" })}` : plan.tagline}
                </p>
                {data.hasBillingAccount && (
                  <form action="/api/stripe/portal" method="post" className="mt-5">
                    <button className="btn-ghost">
                      <CreditCard size={15} /> Manage billing, invoices or cancel
                    </button>
                  </form>
                )}
              </div>
              <div className="rounded-xl border border-line bg-panel-2 p-5">
                <p className="flex items-center gap-2 text-sm font-medium">
                  <Sparkles size={15} className="text-accent" /> Included AI this month
                </p>
                <p className="mt-3 text-2xl font-semibold">
                  {data.aiUsed.toLocaleString()}
                  <span className="text-sm font-normal text-muted"> / {plan.includedAiTokens.toLocaleString()} tokens</span>
                </p>
                <ProgressBar value={pct} className="mt-3" />
                <p className="mt-2 text-xs text-muted">
                  Resets on the 1st. {data.maskedKey ? "Your own key takes over after that." : "Add your own key for unlimited AI."}
                </p>
              </div>
            </div>
            <div className="pt-4">
              <PricingTable signedIn currentPlan={plan.id} />
            </div>
          </Section>

          <Section
            id="ai"
            title="AI"
            description={
              plan.id === "studio"
                ? "Optional on Studio. Your own key is only used after the included monthly AI runs out."
                : "Optional. Add a Groq (free tier available at console.groq.com) or OpenAI key for unlimited AI. It's encrypted before it's stored."
            }
          >
            <div className="card p-6">
              <div className="flex items-center gap-2 font-medium">
                <KeyRound size={16} className="text-accent" /> Your AI key
                {data.maskedKey ? <Badge tone="accent">Saved</Badge> : <Badge>Not set</Badge>}
              </div>
              <AiKeyForm provider={data.aiProvider} model={data.aiModel} maskedKey={data.maskedKey} />
            </div>
          </Section>

          <Section id="account" title="Account" description={`Signed in as ${data.email}`}>
            {!flash.reset && <ChangePasswordForm highlight={false} />}
            <DeleteAccountForm email={data.email} />
          </Section>
        </div>
      </div>
    </div>
  );
}
