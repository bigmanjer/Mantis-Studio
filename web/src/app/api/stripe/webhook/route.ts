import { NextResponse } from "next/server";
import type Stripe from "stripe";
import { planForPriceId } from "@/lib/plans";
import { stripe } from "@/lib/stripe";
import { createAdminClient } from "@/lib/supabase/server";

// Stripe -> Developers -> Webhooks -> add endpoint https://YOUR-SITE/api/stripe/webhook
// Events: checkout.session.completed, customer.subscription.created/updated/deleted
export async function POST(req: Request) {
  const sig = req.headers.get("stripe-signature");
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!sig || !secret) return NextResponse.json({ error: "Missing signature" }, { status: 400 });

  let event: Stripe.Event;
  try {
    event = stripe().webhooks.constructEvent(await req.text(), sig, secret);
  } catch {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;
      if (session.subscription) {
        const sub = await stripe().subscriptions.retrieve(session.subscription as string);
        await syncSubscription(sub, session.client_reference_id);
      }
      break;
    }
    case "customer.subscription.created":
    case "customer.subscription.updated":
    case "customer.subscription.deleted":
      await syncSubscription(event.data.object as Stripe.Subscription);
      break;
  }
  return NextResponse.json({ received: true });
}

async function syncSubscription(eventSub: Stripe.Subscription, userIdHint?: string | null) {
  const admin = createAdminClient();
  // Webhooks can arrive out of order; always read the subscription's current state from Stripe.
  const sub = await stripe().subscriptions.retrieve(eventSub.id);
  const customerId = typeof sub.customer === "string" ? sub.customer : sub.customer.id;
  const active = ["active", "trialing", "past_due"].includes(sub.status);
  const item = sub.items.data[0];
  const plan = active ? planForPriceId(item?.price.id) : "free";
  const periodEnd = item?.current_period_end;

  const update = {
    plan,
    stripe_customer_id: customerId,
    stripe_subscription_id: sub.id,
    subscription_status: sub.status,
    current_period_end: periodEnd ? new Date(periodEnd * 1000).toISOString() : null,
  };

  const userId = userIdHint || sub.metadata?.user_id;
  const query = admin.from("profiles").update(update);
  const { error } = userId ? await query.eq("id", userId) : await query.eq("stripe_customer_id", customerId);
  if (error) console.error("Stripe sync failed", error);
}
