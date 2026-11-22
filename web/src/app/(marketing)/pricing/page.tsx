import PricingTable from "@/components/billing/PricingTable";
import Comparison from "@/components/marketing/Comparison";
import Faq from "@/components/marketing/Faq";
import { getOptionalUser, getProfile } from "@/lib/supabase/server";

export const metadata = { title: "Pricing" };

export default async function PricingPage() {
  const user = await getOptionalUser();
  const profile = user ? await getProfile(user.id, user.email).catch(() => null) : null;
  return (
    <div className="relative">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(50%_60%_at_50%_0%,var(--accent-soft),transparent)]" />
      <div className="relative mx-auto max-w-6xl px-4 py-16 sm:py-24">
        <div className="mb-12 text-center">
          <p className="eyebrow">Pricing</p>
          <h1 className="mt-3 font-serif text-4xl font-semibold sm:text-5xl">Pricing</h1>
          <p className="mx-auto mt-4 max-w-xl text-muted">
            Start free. Pay when it’s worth it to you. Cancel whenever you like.
          </p>
        </div>
        <PricingTable signedIn={!!user} currentPlan={profile?.plan} />
        <div className="mx-auto mt-24 max-w-4xl">
          <h2 className="mb-8 text-center font-serif text-3xl font-semibold">How MANTIS compares</h2>
          <Comparison />
        </div>
        <div className="mx-auto mt-24 max-w-3xl">
          <h2 className="mb-8 text-center font-serif text-3xl font-semibold">Good questions</h2>
          <Faq />
        </div>
      </div>
    </div>
  );
}
