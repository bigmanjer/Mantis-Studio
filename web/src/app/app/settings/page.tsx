import SettingsView from "@/components/app/SettingsView";
import { decrypt, maskKey } from "@/lib/crypto";
import { currentPeriod, getPlan } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";

export const metadata = { title: "Settings" };

export default async function SettingsPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const { supabase, user } = await requireUser();
  const [profile, { data: usage }] = await Promise.all([
    getProfile(user!.id, user!.email),
    supabase.from("ai_usage").select("tokens").eq("period", currentPeriod()).maybeSingle(),
  ]);

  let maskedKey: string | null = null;
  if (profile.ai_key_encrypted) {
    try {
      maskedKey = maskKey(decrypt(profile.ai_key_encrypted));
    } catch {
      maskedKey = "unreadable, please re-enter";
    }
  }

  return (
    <SettingsView
      data={{
        email: user!.email ?? "",
        plan: getPlan(profile.plan),
        subscriptionStatus: profile.subscription_status,
        periodEnd: profile.current_period_end,
        hasBillingAccount: !!profile.stripe_customer_id,
        aiUsed: usage?.tokens ?? 0,
        aiProvider: profile.ai_provider,
        aiModel: profile.ai_model ?? "",
        maskedKey,
      }}
      flash={{
        checkout: sp.checkout,
        upgrade: sp.upgrade === "pro" || sp.upgrade === "studio" ? sp.upgrade : undefined,
        interval: sp.interval === "month" ? "month" : "year",
        reset: sp.reset === "1",
      }}
    />
  );
}
