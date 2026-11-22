import "server-only";
import Stripe from "stripe";

let client: Stripe | null = null;

export function stripe(): Stripe {
  if (!process.env.STRIPE_SECRET_KEY) throw new Error("STRIPE_SECRET_KEY is not set");
  client ??= new Stripe(process.env.STRIPE_SECRET_KEY);
  return client;
}

export function siteUrl(req?: Request): string {
  return process.env.NEXT_PUBLIC_SITE_URL || (req ? new URL(req.url).origin : "http://localhost:3000");
}
