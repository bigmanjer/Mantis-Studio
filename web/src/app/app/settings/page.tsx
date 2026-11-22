import { ChangePasswordForm, DeleteAccountForm } from "@/components/AccountForms";
import AiKeyForm from "@/components/AiKeyForm";
import PricingCards from "@/components/PricingCards";
import UpgradeButton from "@/components/UpgradeButton";
import { decrypt, maskKey } from "@/lib/crypto";
import { currentPeriod, getPlan, type PlanId } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";

export default async function SettingsPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const { supabase, user } = await requireUser();
  const profile = await getProfile(user!.id, user!.email);
  const plan = getPlan(profile.plan);
  const { data: usage } = await supabase.from("ai_usage").select("tokens, requests").eq("period", currentPeriod()).maybeSingle();

  let maskedKey: string | null = null;
  if (profile.ai_key_encrypted) {
    try {
      maskedKey = maskKey(decrypt(profile.ai_key_encrypted));
    } catch {
      maskedKey = "(unreadable — please re-enter)";
    }
  }
  const upgrade = sp.upgrade as PlanId | undefined;
  const usedPct = plan.includedAiTokens ? Math.min(100, Math.round(((usage?.tokens ?? 0) / plan.includedAiTokens) * 100)) : 0;

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-10">
      <h1 className="text-3xl font-semibold">Settings & billing</h1>

      {sp.reset === "1" && <ChangePasswordForm highlight />}

      {sp.checkout === "success" && (
        <p className="card border-accent/50 p-4 text-sm text-accent">
          Thanks for subscribing! Your plan updates within a few seconds — refresh if it still shows the old plan.
        </p>
      )}
      {sp.checkout === "canceled" && <p className="card p-4 text-sm text-muted">Checkout canceled. You haven&apos;t been charged.</p>}
      {upgrade && (upgrade === "pro" || upgrade === "studio") && plan.id === "free" && (
        <div className="card flex flex-wrap items-center justify-between gap-3 border-accent/50 p-4">
          <p className="text-sm">Finish upgrading to {getPlan(upgrade).name}.</p>
          <UpgradeButton plan={upgrade} interval={sp.interval === "month" ? "month" : "year"} className="btn-primary">
            Continue to checkout
          </UpgradeButton>
        </div>
      )}

      <section className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="label">Current plan</p>
            <p className="text-2xl font-semibold text-accent">{plan.name}</p>
            {profile.subscription_status && profile.plan !== "free" && (
              <p className="mt-1 text-sm text-muted">
                Status: {profile.subscription_status}
                {profile.current_period_end && ` · renews ${new Date(profile.current_period_end).toLocaleDateString()}`}
              </p>
            )}
          </div>
          {profile.stripe_customer_id && (
            <form action="/api/stripe/portal" method="post">
              <button className="btn-ghost">Manage billing / cancel</button>
            </form>
          )}
        </div>
        {plan.includedAiTokens > 0 && (
          <div className="mt-6">
            <p className="text-sm">
              Included AI this month: {(usage?.tokens ?? 0).toLocaleString()} / {plan.includedAiTokens.toLocaleString()} tokens
            </p>
            <div className="mt-2 h-2 rounded-full bg-panel-2">
              <div className="h-2 rounded-full bg-accent" style={{ width: `${usedPct}%` }} />
            </div>
          </div>
        )}
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold">Your AI key</h2>
        <p className="mt-1 text-sm text-muted">
          {plan.id === "studio"
            ? "Optional on Studio — used only after your included monthly AI runs out."
            : "Optional. Your plan includes a small monthly AI allowance; add a key for unlimited AI. Get a free key at console.groq.com, or use an OpenAI key. It's encrypted before it's stored."}
        </p>
        <AiKeyForm provider={profile.ai_provider} model={profile.ai_model ?? ""} maskedKey={maskedKey} />
      </section>

      <section id="plans" className="scroll-mt-6">
        <h2 className="mb-4 text-lg font-semibold">Plans</h2>
        <PricingCards signedIn currentPlan={plan.id} />
      </section>
      <section className="space-y-6">
        <h2 className="text-lg font-semibold">Account</h2>
        <p className="text-sm text-muted">Signed in as {user!.email}</p>
        {sp.reset !== "1" && <ChangePasswordForm highlight={false} />}
        <DeleteAccountForm email={user!.email ?? ""} />
      </section>
    </div>
  );
}
