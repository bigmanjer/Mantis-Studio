import PricingCards from "@/components/PricingCards";
import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";
import { getOptionalUser, getProfile } from "@/lib/supabase/server";

export const metadata = { title: "Pricing" };

const FAQ = [
  [
    "What does \"bring your own key\" mean?",
    "You paste an API key from Groq (free tier available) or OpenAI into Settings. AI requests are billed to that account, not to us. Your key is stored encrypted.",
  ],
  [
    "Can I try the AI before paying?",
    "Yes. Every account gets 25k AI tokens a month free — enough to draft a few scenes — with no key or card needed.",
  ],
  [
    "What happens on Studio when I use up the included AI?",
    "If you've saved your own key, MANTIS switches to it automatically. Otherwise AI pauses until your allowance resets next month.",
  ],
  ["Can I cancel any time?", "Yes. Manage or cancel your subscription from Settings. You keep access until the end of the billing period."],
  [
    "What happens to my projects if I downgrade?",
    "Nothing is deleted. On Free you can still open and edit everything, but you can't create new projects beyond the limit.",
  ],
];

export default async function PricingPage() {
  const user = await getOptionalUser();
  const profile = user ? await getProfile(user.id, user.email).catch(() => null) : null;
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-6xl px-4 py-16 sm:py-24">
        <div className="mb-14 text-center">
          <h1 className="font-serif text-4xl font-semibold sm:text-5xl">Simple pricing</h1>
          <p className="mt-4 text-muted">Start free. Upgrade when your book needs more.</p>
        </div>
        <PricingCards signedIn={!!user} currentPlan={profile?.plan} />
        <div className="mx-auto mt-20 max-w-3xl">
          <h2 className="mb-6 text-2xl font-semibold">Questions</h2>
          <div className="space-y-4">
            {FAQ.map(([q, a]) => (
              <div key={q} className="card p-5">
                <p className="font-medium">{q}</p>
                <p className="mt-2 text-sm text-muted">{a}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
