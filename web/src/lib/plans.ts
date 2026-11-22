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
    tagline: "Try it on a real book.",
    maxProjects: 2,
    byokAi: true,
    includedAiTokens: 25_000,
    docxExport: false,
    features: [
      "2 projects",
      "Outline, chapter editor & World Bible",
      "Free AI to try (25k tokens a month)",
      "Unlimited AI with your own Groq or OpenAI key",
      "Markdown & text export",
    ],
  },
  pro: {
    id: "pro",
    name: "Pro",
    monthly: 9,
    yearly: 90,
    tagline: "For when you mean to finish.",
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
    tagline: "Everything, with the AI already paid for.",
    maxProjects: Infinity,
    byokAi: true,
    includedAiTokens: 1_000_000,
    docxExport: true,
    features: [
      "Everything in Pro",
      "1M AI tokens a month (roughly 150 chapter drafts)",
      "Switches to your own key if you run out",
      "Priority email support",
    ],
  },
};

export function getPlan(id: string | null | undefined): Plan {
  return PLANS[(id as PlanId) in PLANS ? (id as PlanId) : "free"];
}

export function currentPeriod(d = new Date()): string {
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}
