import "server-only";
import Stripe from "stripe";
import { env, siteUrl as configuredSiteUrl } from "./env";
import { PLANS, type Interval, type PlanId } from "./plans";
import { createAdminClient } from "./supabase/server";

let client: Stripe | null = null;

export function stripeConfigured(): boolean {
  return !!env.stripeSecretKey;
}

export function stripe(): Stripe {
  if (!env.stripeSecretKey) throw new Error("Stripe is not connected yet.");
  client ??= new Stripe(env.stripeSecretKey);
  return client;
}

export function siteUrl(): string {
  return configuredSiteUrl();
}

// ---------- Prices ----------
// Prices are found by a stable lookup key and created on first use, so nobody has to
// create products in the Stripe dashboard or copy price IDs into settings.
const lookupKey = (plan: PlanId, interval: Interval) => `mantis_${plan}_${interval}ly`;

const priceCache = new Map<string, string>();

export async function ensurePriceId(plan: PlanId, interval: Interval): Promise<string> {
  if (plan === "free") throw new Error("The free plan has no price.");
  // Explicit overrides still win, for anyone who prefers dashboard-managed prices.
  const override =
    plan === "pro"
      ? interval === "year"
        ? process.env.STRIPE_PRICE_PRO_YEARLY
        : process.env.STRIPE_PRICE_PRO
      : interval === "year"
        ? process.env.STRIPE_PRICE_STUDIO_YEARLY
        : process.env.STRIPE_PRICE_STUDIO;
  if (override) return override;

  const key = lookupKey(plan, interval);
  const cached = priceCache.get(key);
  if (cached) return cached;

  const s = stripe();
  const found = await s.prices.list({ lookup_keys: [key], active: true, limit: 1 });
  if (found.data[0]) {
    priceCache.set(key, found.data[0].id);
    return found.data[0].id;
  }

  const p = PLANS[plan];
  const productId = `mantis_${plan}`;
  let product: Stripe.Product;
  try {
    product = await s.products.retrieve(productId);
  } catch {
    product = await s.products.create({ id: productId, name: `MANTIS Studio ${p.name}`, description: p.tagline });
  }
  const price = await s.prices.create({
    product: product.id,
    currency: "usd",
    unit_amount: Math.round((interval === "year" ? p.yearly : p.monthly) * 100),
    recurring: { interval },
    lookup_key: key,
    transfer_lookup_key: true,
    metadata: { plan, interval },
  });
  priceCache.set(key, price.id);
  return price.id;
}

/** Which plan a Stripe price belongs to (from our metadata/lookup key, or env overrides). */
export function planForPrice(price: Stripe.Price | null | undefined): PlanId {
  if (!price) return "free";
  const meta = price.metadata?.plan;
  if (meta === "pro" || meta === "studio") return meta;
  if (price.lookup_key?.startsWith("mantis_studio_")) return "studio";
  if (price.lookup_key?.startsWith("mantis_pro_")) return "pro";
  const e = process.env;
  if (price.id === e.STRIPE_PRICE_STUDIO || price.id === e.STRIPE_PRICE_STUDIO_YEARLY) return "studio";
  if (price.id === e.STRIPE_PRICE_PRO || price.id === e.STRIPE_PRICE_PRO_YEARLY) return "pro";
  return "free";
}

// ---------- Customer portal ----------
let portalConfigId: string | null = null;

/**
 * New Stripe accounts have no customer-portal configuration, which makes
 * billingPortal.sessions.create fail. Create one on first use: invoices, card updates,
 * cancel at period end, and switching between Pro/Studio monthly/yearly.
 */
export async function ensurePortalConfiguration(): Promise<string> {
  if (portalConfigId) return portalConfigId;
  const s = stripe();
  const existing = await s.billingPortal.configurations.list({ active: true, limit: 1 });
  if (existing.data[0]) return (portalConfigId = existing.data[0].id);

  const [proM, proY, stuM, stuY] = await Promise.all([
    ensurePriceId("pro", "month"),
    ensurePriceId("pro", "year"),
    ensurePriceId("studio", "month"),
    ensurePriceId("studio", "year"),
  ]);
  const proPrice = await s.prices.retrieve(proM);
  const stuPrice = await s.prices.retrieve(stuM);
  const config = await s.billingPortal.configurations.create({
    business_profile: { headline: "Manage your MANTIS Studio subscription" },
    features: {
      invoice_history: { enabled: true },
      payment_method_update: { enabled: true },
      customer_update: { enabled: true, allowed_updates: ["email", "address"] },
      subscription_cancel: { enabled: true, mode: "at_period_end" },
      subscription_update: {
        enabled: true,
        default_allowed_updates: ["price"],
        proration_behavior: "create_prorations",
        products: [
          { product: proPrice.product as string, prices: [proM, proY] },
          { product: stuPrice.product as string, prices: [stuM, stuY] },
        ],
      },
    },
  });
  return (portalConfigId = config.id);
}

// ---------- Subscription sync ----------
const ACTIVE = new Set(["active", "trialing", "past_due"]);

/** Write a subscription's current state onto the user's profile. */
export async function syncSubscription(subId: string, userIdHint?: string | null): Promise<void> {
  const sub = await stripe().subscriptions.retrieve(subId, { expand: ["items.data.price"] });
  const customerId = typeof sub.customer === "string" ? sub.customer : sub.customer.id;
  const item = sub.items.data[0];
  const plan = ACTIVE.has(sub.status) ? planForPrice(item?.price) : "free";
  const periodEnd = item?.current_period_end;
  const update = {
    plan,
    stripe_customer_id: customerId,
    stripe_subscription_id: sub.id,
    subscription_status: sub.status,
    current_period_end: periodEnd ? new Date(periodEnd * 1000).toISOString() : null,
  };
  const admin = createAdminClient();
  const userId = userIdHint || sub.metadata?.user_id;
  const q = admin.from("profiles").update(update);
  const { error } = userId ? await q.eq("id", userId) : await q.eq("stripe_customer_id", customerId);
  if (error) console.error("Stripe sync failed", error);
}

/**
 * Re-check a customer's subscriptions with Stripe (used when someone returns from checkout or
 * opens Settings). This keeps plans correct even if a webhook was missed or not configured.
 */
export async function syncCustomer(customerId: string, userId: string): Promise<void> {
  if (!stripeConfigured()) return;
  const subs = await stripe().subscriptions.list({ customer: customerId, status: "all", limit: 10 });
  const best = subs.data.find((s) => ACTIVE.has(s.status)) ?? subs.data[0];
  if (best) {
    await syncSubscription(best.id, userId);
  } else {
    await createAdminClient()
      .from("profiles")
      .update({ plan: "free", subscription_status: null, stripe_subscription_id: null, current_period_end: null })
      .eq("id", userId);
  }
}
