// Public Supabase settings, safe for browser, server and middleware.
// Written as literal process.env reads so Next.js can inline them into the browser bundle.
// Accepts both the classic anon key and the newer "publishable" key name that
// Vercel's Supabase integration may provide.
export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
export const SUPABASE_ANON_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "";

export const supabaseConfigured = () => !!(SUPABASE_URL && SUPABASE_ANON_KEY);
