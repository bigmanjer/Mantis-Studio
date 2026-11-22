import { redirect } from "next/navigation";
import AppShell from "@/components/app/AppShell";
import { currentPeriod, getPlan } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  const [profile, { data: usage }] = await Promise.all([
    getProfile(user.id, user.email),
    supabase.from("ai_usage").select("tokens").eq("period", currentPeriod()).maybeSingle(),
  ]);
  const plan = getPlan(profile.plan);

  return (
    <AppShell
      user={{
        email: user.email ?? "",
        planId: plan.id,
        planName: plan.name,
        aiUsed: usage?.tokens ?? 0,
        aiLimit: plan.includedAiTokens,
      }}
    >
      {children}
    </AppShell>
  );
}
