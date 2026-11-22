import { NextResponse } from "next/server";
import type Stripe from "stripe";
import { env } from "@/lib/env";
import { stripe, syncSubscription } from "@/lib/stripe";

// Optional: Stripe -> Developers -> Webhooks -> https://YOUR-SITE/api/stripe/webhook
// Events: checkout.session.completed, customer.subscription.created/updated/deleted
//
// If STRIPE_WEBHOOK_SECRET is set, the signature is verified. If not, the event is
// re-fetched from Stripe by its ID with our secret key, so forged payloads are ignored.
// Plans are also re-synced when users return from checkout or open Settings.
export async function POST(req: Request) {
  const body = await req.text();
  let event: Stripe.Event;
  try {
    if (env.stripeWebhookSecret) {
      const sig = req.headers.get("stripe-signature") ?? "";
      event = stripe().webhooks.constructEvent(body, sig, env.stripeWebhookSecret);
    } else {
      const id = (JSON.parse(body) as { id?: string }).id;
      if (!id || !id.startsWith("evt_")) throw new Error("no event id");
      event = await stripe().events.retrieve(id);
    }
  } catch {
    return NextResponse.json({ error: "Invalid event" }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;
      if (session.subscription) await syncSubscription(session.subscription as string, session.client_reference_id);
      break;
    }
    case "customer.subscription.created":
    case "customer.subscription.updated":
    case "customer.subscription.deleted":
      await syncSubscription((event.data.object as Stripe.Subscription).id);
      break;
  }
  return NextResponse.json({ received: true });
}
