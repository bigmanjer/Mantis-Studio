"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { PROVIDERS, type ProviderId } from "@/lib/ai";
import { encrypt } from "@/lib/crypto";
import { getPlan } from "@/lib/plans";
import { createAdminClient, getProfile, requireUser } from "@/lib/supabase/server";

export async function createProject(formData: FormData): Promise<{ error?: string } | void> {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");

  const profile = await getProfile(user.id, user.email);
  const plan = getPlan(profile.plan);
  const { count } = await supabase.from("projects").select("id", { count: "exact", head: true });
  if ((count ?? 0) >= plan.maxProjects) {
    return { error: `The ${plan.name} plan includes ${plan.maxProjects} projects. Upgrade for unlimited projects.` };
  }

  const title = String(formData.get("title") || "").trim().slice(0, 200) || "Untitled Project";
  const genre = String(formData.get("genre") || "").trim().slice(0, 100);
  const premise = String(formData.get("premise") || "").trim().slice(0, 5000);
  const { data, error } = await supabase
    .from("projects")
    .insert({ title, genre, premise, user_id: user.id })
    .select("id")
    .single();
  if (error) {
    return { error: error.message.includes("PLAN_LIMIT") ? error.message.replace(/^.*PLAN_LIMIT:\s*/, "") : error.message };
  }
  await supabase.from("chapters").insert({ project_id: data.id, user_id: user.id, position: 1, title: "Chapter 1" });
  redirect(`/app/projects/${data.id}`);
}

export async function deleteProject(projectId: string) {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  await supabase.from("projects").delete().eq("id", projectId);
  revalidatePath("/app");
  redirect("/app");
}

/** Permanently deletes the account: cancels any subscription, then removes the user (all data cascades). */
export async function deleteAccount(confirmEmail: string): Promise<{ error?: string } | void> {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  if (confirmEmail.trim().toLowerCase() !== (user.email ?? "").toLowerCase()) {
    return { error: "Type your account email exactly to confirm." };
  }
  const profile = await getProfile(user.id, user.email);
  if (profile.stripe_subscription_id && profile.subscription_status !== "canceled") {
    try {
      const { stripe } = await import("@/lib/stripe");
      await stripe().subscriptions.cancel(profile.stripe_subscription_id);
    } catch (e) {
      console.error("Subscription cancel failed during account deletion", e);
      return { error: "We couldn't cancel your subscription automatically. Cancel it under Manage billing first, then try again." };
    }
  }
  const { error } = await createAdminClient().auth.admin.deleteUser(user.id);
  if (error) return { error: error.message };
  await supabase.auth.signOut();
  redirect("/?deleted=1");
}

export async function saveAiSettings(formData: FormData): Promise<{ error?: string; ok?: boolean }> {
  const { user } = await requireUser();
  if (!user) return { error: "Please log in." };
  const provider = String(formData.get("provider") || "groq") as ProviderId;
  if (!(provider in PROVIDERS)) return { error: "Unknown provider." };
  const model = String(formData.get("model") || "").trim().slice(0, 100) || null;
  const key = String(formData.get("apiKey") || "").trim();
  const clear = formData.get("clear") === "1";

  const update: Record<string, unknown> = { ai_provider: provider, ai_model: model };
  if (clear) update.ai_key_encrypted = null;
  else if (key) {
    if (key.length < 20 || key.length > 300 || /\s/.test(key)) return { error: "That doesn't look like a valid API key." };
    update.ai_key_encrypted = encrypt(key);
  }
  const admin = createAdminClient();
  await getProfile(user.id, user.email);
  const { error } = await admin.from("profiles").update(update).eq("id", user.id);
  if (error) return { error: error.message };
  revalidatePath("/app/settings");
  return { ok: true };
}
