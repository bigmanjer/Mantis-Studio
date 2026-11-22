import { NextResponse } from "next/server";
import { stripe, stripeConfigured } from "@/lib/stripe";
import { getProfile, requireUser } from "@/lib/supabase/server";

export async function POST(req: Request) {
  const { user } = await requireUser();
  if (!user) return NextResponse.redirect(new URL("/login", req.url), { status: 303 });
  const profile = await getProfile(user.id, user.email);
  if (!stripeConfigured() || !profile.stripe_customer_id) {
    return NextResponse.redirect(new URL("/app/settings#billing", req.url), { status: 303 });
  }
  const session = await stripe().billingPortal.sessions.create({
    customer: profile.stripe_customer_id,
    return_url: `${new URL(req.url).origin}/app/settings`,
  });
  return NextResponse.redirect(session.url, { status: 303 });
}
