# MANTIS Studio Web — Setup Guide

The website lives in this `web/` folder. It's a Next.js app that uses **Supabase** for accounts and data,
**Stripe** for subscriptions, and is designed to be hosted on **Vercel**.

You only need to do the account steps once. Use **test mode** in Stripe until everything works.

---

## 1. Supabase (accounts + database) — free tier is fine

1. Go to supabase.com → **New project**. Pick a strong database password and save it somewhere safe.
2. When it's ready, open **SQL Editor → New query**, paste the whole contents of `supabase/schema.sql`, and click **Run**.
3. Open **Project Settings → API** and copy:
   - Project URL → `NEXT_PUBLIC_SUPABASE_URL`
   - `anon` public key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (**secret** — never share it or put it in the browser)
4. **Authentication → Providers → Email**: keep **Confirm email** ON (stops people farming free AI with fake accounts).
5. **Authentication → SMTP Settings**: Supabase's built-in email only sends a few messages per hour — fine for testing,
   not for launch. Connect Resend (you already have it set up for the old app) before going live.
6. **Authentication → URL Configuration**: set Site URL to `http://localhost:3000` for now (change to your real domain later)
   and add `http://localhost:3000/auth/callback` and `https://YOUR-DOMAIN/auth/callback` to Redirect URLs.

## 2. Stripe (subscriptions)

1. Create a Stripe account and stay in **Test mode** (toggle top-right).
2. **Product catalog → Add product**:
   - "MANTIS Pro" with two prices: $9 / month → `STRIPE_PRICE_PRO`, and $90 / year → `STRIPE_PRICE_PRO_YEARLY`
   - "MANTIS Studio" with two prices: $19 / month → `STRIPE_PRICE_STUDIO`, and $190 / year → `STRIPE_PRICE_STUDIO_YEARLY`
   - Copy each **price ID** (starts with `price_…`).
3. **Developers → API keys** → Secret key → `STRIPE_SECRET_KEY`
4. **Settings → Billing → Customer portal** → turn it on, allow cancelling and switching between the two products.
5. Webhook (after the site is deployed): **Developers → Webhooks → Add endpoint**
   - URL: `https://YOUR-DOMAIN/api/stripe/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`
   - Copy the signing secret → `STRIPE_WEBHOOK_SECRET`
   - For local testing instead, install the Stripe CLI and run `stripe listen --forward-to localhost:3000/api/stripe/webhook`.

## 3. AI for the Studio plan

Get a Groq key from console.groq.com → `MANTIS_GROQ_API_KEY`. This pays for the included AI: 1M tokens/month per
Studio user and a 25k-token free taste for everyone else (change `includedAiTokens` in `src/lib/plans.ts`).
At Groq's Llama 3.3 70B pricing that's roughly $0.70 per Studio user per month at full use, and about 2¢ per free user.
Set a monthly spend limit in the Groq console so a bug or abuse can never run up a large bill.

## 4. Run it on your computer

```powershell
cd web
copy .env.example .env.local
# open .env.local and fill in the values from the steps above
# MANTIS_ENCRYPTION_SECRET: any random string of 32+ characters (keep it forever — changing it makes saved user keys unreadable)
npm install
npm run dev
```

Open http://localhost:3000. Stripe's test card is `4242 4242 4242 4242`, any future date, any CVC.

## 5. Put it on the web (Vercel)

1. Push this repo to GitHub.
2. vercel.com → **Add New → Project** → import `Mantis-Studio` → set **Root Directory** to `web`.
3. Add every variable from `.env.local` under **Environment Variables**, with `NEXT_PUBLIC_SITE_URL` set to your real URL.
4. Deploy, then add your custom domain under **Settings → Domains**.
5. Update the Supabase Site URL / redirect URLs and create the Stripe webhook (steps 1.6 and 2.5) with the real domain.
6. When you're ready to take real money: switch Stripe to **live mode**, recreate the two products, and replace the
   Stripe keys, price IDs and webhook secret in Vercel.

## Before you take real money

- Set `NEXT_PUBLIC_SUPPORT_EMAIL` to a real inbox and `NEXT_PUBLIC_LEGAL_EFFECTIVE_DATE` to your launch date.
- Have the Terms and Privacy pages (`content/legal/`) reviewed by a lawyer for your country — they're a solid draft, not legal advice.
- In Stripe, turn on **Stripe Tax** if you need to collect sales tax/VAT, and fill in your public business details.

## Changing prices or limits

- Prices shown on the site: `src/lib/plans.ts` (the actual charge comes from Stripe).
- Free plan project limit: `src/lib/plans.ts` **and** the `enforce_project_limit` function in `supabase/schema.sql`.
