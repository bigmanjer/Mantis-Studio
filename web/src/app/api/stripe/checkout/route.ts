import { NextResponse } from "next/server";
import type { Interval, PlanId } from "@/lib/plans";
import { ensurePriceId, stripe, stripeConfigured } from "@/lib/stripe";
import { createAdminClient, getProfile, requireUser } from "@/lib/supabase/server";

export async function POST(req: Request) {
  const { user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Please log in." }, { status: 401 });
  if (!stripeConfigured()) return NextResponse.json({ error: "Payments aren't switched on yet. Please try again soon." }, { status: 503 });

  const { plan, interval } = (await req.json().catch(() => ({}))) as { plan?: PlanId; interval?: Interval };
  if (plan !== "pro" && plan !== "studio") return NextResponse.json({ error: "Unknown plan." }, { status: 400 });

  const base = new URL(req.url).origin;
  const s = stripe();
  const profile = await getProfile(user.id, user.email);

  // Already subscribed: plan changes and cancellation happen in Stripe's customer portal.
  if (profile.stripe_customer_id && profile.plan !== "free" && profile.subscription_status !== "canceled") {
    const portal = await s.billingPortal.sessions.create({ customer: profile.stripe_customer_id, return_url: `${base}/app/settings` });
    return NextResponse.json({ url: portal.url });
  }

  try {
    const price = await ensurePriceId(plan, interval === "month" ? "month" : "year");

    let customerId = profile.stripe_customer_id;
    if (!customerId) {
      const customer = await s.customers.create({ email: user.email ?? undefined, metadata: { user_id: user.id } });
      customerId = customer.id;
      await createAdminClient().from("profiles").update({ stripe_customer_id: customerId }).eq("id", user.id);
    }

    const session = await s.checkout.sessions.create({
      mode: "subscription",
      customer: customerId,
      client_reference_id: user.id,
      line_items: [{ price, quantity: 1 }],
      allow_promotion_codes: true,
      subscription_data: { metadata: { user_id: user.id } },
      success_url: `${base}/app/settings?checkout=success`,
      cancel_url: `${base}/app/settings?checkout=canceled`,
    });
    return NextResponse.json({ url: session.url });
  } catch (e) {
    console.error("Checkout failed", e);
    return NextResponse.json({ error: "We couldn't start checkout. Please try again in a minute." }, { status: 502 });
  }
}
