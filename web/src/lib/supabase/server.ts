import { createServerClient } from "@supabase/ssr";
import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";
import { env } from "@/lib/env";
import { SUPABASE_ANON_KEY, SUPABASE_URL, supabaseConfigured } from "./config";

/** Supabase client acting as the signed-in user (RLS applies). */
export async function createClient() {
  const cookieStore = await cookies();
  return createServerClient(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (list) => {
          try {
            list.forEach(({ name, value, options }) => cookieStore.set(name, value, options));
          } catch {
            // Called from a Server Component; middleware refreshes the session instead.
          }
        },
      },
    },
  );
}

/** Service-role client. Server only — bypasses RLS. Never import into client code. */
export function createAdminClient() {
  return createSupabaseClient(
    SUPABASE_URL,
    env.supabaseServiceKey,
    { auth: { persistSession: false, autoRefreshToken: false } },
  );
}

export { supabaseConfigured };

/** Current user or null. Safe on public pages even before Supabase is configured. */
export async function getOptionalUser() {
  if (!supabaseConfigured()) return null;
  try {
    const supabase = await createClient();
    return (await supabase.auth.getUser()).data.user;
  } catch {
    return null;
  }
}

export async function requireUser() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getUser();
  return { supabase, user: data.user };
}

export interface Profile {
  id: string;
  email: string | null;
  plan: "free" | "pro" | "studio";
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  subscription_status: string | null;
  current_period_end: string | null;
  ai_provider: "groq" | "openai";
  ai_model: string | null;
  ai_key_encrypted: string | null;
}

/** Profile for a user id, created on demand if the signup trigger hasn't run. Server only. */
export async function getProfile(userId: string, email?: string | null): Promise<Profile> {
  const admin = createAdminClient();
  const { data } = await admin.from("profiles").select("*").eq("id", userId).maybeSingle();
  if (data) return data as Profile;
  const { data: created, error } = await admin
    .from("profiles")
    .upsert({ id: userId, email: email ?? null })
    .select("*")
    .single();
  if (error) throw error;
  return created as Profile;
}
