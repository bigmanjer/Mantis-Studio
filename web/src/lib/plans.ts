export type PlanId = "free" | "pro" | "studio";
export type Interval = "month" | "year";

export interface Plan {
  id: PlanId;
  name: string;
  monthly: number; // display price in USD; real price lives in Stripe
  yearly: number; // display price per year (2 months free)
  tagline: string;
  maxProjects: number; // Infinity = unlimited
  byokAi: boolean; // may use their own Groq/OpenAI key
  includedAiTokens: number; // monthly tokens paid for by MANTIS (0 = none)
  docxExport: boolean;
  features: string[];
}

// Positioning (Nov 2026): Novelcrafter is $4-20/mo and bring-your-own-key only;
// Sudowrite is $19-59/mo with credits. MANTIS undercuts both on AI included per dollar
// and is the only one with a free tier that includes some AI.
export const PLANS: Record<PlanId, Plan> = {
  free: {
    id: "free",
    name: "Free",
    monthly: 0,
    yearly: 0,
    tagline: "Everything you need to start a book.",
    maxProjects: 2,
    byokAi: true,
    includedAiTokens: 25_000,
    docxExport: false,
    features: [
      "2 projects",
      "Outline, chapter editor & World Bible",
      "Try AI free: 25k tokens / month",
      "Unlimited AI with your own Groq/OpenAI key",
      "Markdown & text export",
    ],
  },
  pro: {
    id: "pro",
    name: "Pro",
    monthly: 9,
    yearly: 90,
    tagline: "For writers finishing a manuscript.",
    maxProjects: Infinity,
    byokAi: true,
    includedAiTokens: 25_000,
    docxExport: true,
    features: [
      "Unlimited projects",
      "Everything in Free",
      "Unlimited AI with your own key",
      "Word (.docx) manuscript export",
    ],
  },
  studio: {
    id: "studio",
    name: "Studio",
    monthly: 19,
    yearly: 190,
    tagline: "AI included. No keys, no setup.",
    maxProjects: Infinity,
    byokAi: true,
    includedAiTokens: 1_000_000,
    docxExport: true,
    features: [
      "Everything in Pro",
      "1M AI tokens / month included (~150 chapter drafts)",
      "Falls back to your own key if you run out",
      "Priority email support",
    ],
  },
};

export function getPlan(id: string | null | undefined): Plan {
  return PLANS[(id as PlanId) in PLANS ? (id as PlanId) : "free"];
}

/** Stripe price id for a paid plan and billing interval, from env. Server only. */
export function priceIdFor(plan: PlanId, interval: Interval = "month"): string | undefined {
  const env = process.env;
  if (plan === "pro") return interval === "year" ? env.STRIPE_PRICE_PRO_YEARLY : env.STRIPE_PRICE_PRO;
  if (plan === "studio") return interval === "year" ? env.STRIPE_PRICE_STUDIO_YEARLY : env.STRIPE_PRICE_STUDIO;
  return undefined;
}

export function planForPriceId(priceId: string | null | undefined): PlanId {
  if (!priceId) return "free";
  const env = process.env;
  if (priceId === env.STRIPE_PRICE_STUDIO || priceId === env.STRIPE_PRICE_STUDIO_YEARLY) return "studio";
  if (priceId === env.STRIPE_PRICE_PRO || priceId === env.STRIPE_PRICE_PRO_YEARLY) return "pro";
  return "free";
}

export function currentPeriod(d = new Date()): string {
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}
