import { NextResponse } from "next/server";
import { priceIdFor, type Interval, type PlanId } from "@/lib/plans";
import { siteUrl, stripe } from "@/lib/stripe";
import { createAdminClient, getProfile, requireUser } from "@/lib/supabase/server";

export async function POST(req: Request) {
  const { user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Please log in." }, { status: 401 });
  const { plan, interval } = (await req.json().catch(() => ({}))) as { plan?: PlanId; interval?: Interval };
  const price = plan ? priceIdFor(plan, interval === "year" ? "year" : "month") : undefined;
  if (!price) return NextResponse.json({ error: "Billing isn't set up for that plan yet." }, { status: 400 });

  const profile = await getProfile(user.id, user.email);
  const s = stripe();
  const base = siteUrl(req);

  // Already subscribed: plan changes and cancellation happen in the Stripe customer portal.
  if (profile.stripe_customer_id && profile.plan !== "free" && profile.subscription_status !== "canceled") {
    const portal = await s.billingPortal.sessions.create({
      customer: profile.stripe_customer_id,
      return_url: `${base}/app/settings`,
    });
    return NextResponse.json({ url: portal.url });
  }

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
}
