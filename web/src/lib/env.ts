import "server-only";
import { createHash } from "crypto";

/**
 * Server-side configuration. Accepts both our own variable names and the names that
 * Vercel's Supabase / Groq / Stripe integrations inject automatically, so the site can be
 * configured entirely through those integrations without copying keys by hand.
 */
export const env = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || "",
  supabaseAnonKey:
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.SUPABASE_ANON_KEY ||
    "",
  supabaseServiceKey: process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY || "",
  groqKey: process.env.MANTIS_GROQ_API_KEY || process.env.GROQ_API_KEY || "",
  defaultModel: process.env.MANTIS_DEFAULT_MODEL || "llama-3.3-70b-versatile",
  stripeSecretKey: process.env.STRIPE_SECRET_KEY || "",
  stripeWebhookSecret: process.env.STRIPE_WEBHOOK_SECRET || "",
};

/** Public site URL: explicit setting, else Vercel's production domain, else localhost. */
export function siteUrl(): string {
  if (process.env.NEXT_PUBLIC_SITE_URL) return process.env.NEXT_PUBLIC_SITE_URL.replace(/\/$/, "");
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL) return `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:3000";
}

/**
 * Secret used to encrypt users' own AI keys. Prefer a dedicated MANTIS_ENCRYPTION_SECRET.
 * Without one, derive a separate key from the Supabase service key so the site works out of
 * the box. Note: rotating that service key would make previously saved user AI keys
 * unreadable (users would simply re-enter them).
 */
export function encryptionSecret(): string {
  if (process.env.MANTIS_ENCRYPTION_SECRET && process.env.MANTIS_ENCRYPTION_SECRET.length >= 32) {
    return process.env.MANTIS_ENCRYPTION_SECRET;
  }
  if (env.supabaseServiceKey) {
    return createHash("sha256").update(`mantis-byok-v1:${env.supabaseServiceKey}`).digest("hex");
  }
  throw new Error("Set MANTIS_ENCRYPTION_SECRET (32+ chars) or connect Supabase.");
}
