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
  maxKnowledgeDocs: number; // own reference documents in the Knowledge Base
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
    maxKnowledgeDocs: 3,
    features: [
      "2 projects",
      "Outline, chapter editor & World Bible",
      "Free AI to try (25k tokens a month)",
      "Unlimited AI with your own Groq or OpenAI key",
      "Import a draft and MANTIS organizes it: chapters, World Bible, outline (first book)",
      "Knowledge Base: built-in craft library, 250 author style lenses, 3 of your own documents",
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
    maxKnowledgeDocs: 100,
    features: [
      "Unlimited projects",
      "Everything in Free",
      "Unlimited AI with your own key",
      "World Bible that updates itself and fixes continuity slips as you write",
      "Knowledge Base with 100 of your own documents",
      "Word (.docx) and ebook (.epub) export",
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
    maxKnowledgeDocs: 500,
    features: [
      "Everything in Pro",
      "1M AI tokens a month (roughly 150 chapter drafts)",
      "Switches to your own key if you run out",
      "Priority email support",
    ],
  },
};

/** Automatic World Bible and continuity fixes run on paid plans, or on Free with the writer's own AI key. */
export function autoFeaturesAllowed(profile: { plan?: string | null; is_admin?: boolean | null; ai_key_encrypted?: string | null }): boolean {
  return !!profile.is_admin || (profile.plan ?? "free") !== "free" || !!profile.ai_key_encrypted;
}

export function getPlan(id: string | null | undefined): Plan {
  return PLANS[(id as PlanId) in PLANS ? (id as PlanId) : "free"];
}

/** The plan a profile actually gets. Admin accounts (the business owner) get everything. */
export function planFor(profile: { plan?: string | null; is_admin?: boolean | null }): Plan {
  return getPlan(profile.is_admin ? "studio" : profile.plan);
}

export function currentPeriod(d = new Date()): string {
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}
