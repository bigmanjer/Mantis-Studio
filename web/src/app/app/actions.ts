"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { PROVIDERS, type ProviderId } from "@/lib/ai";
import { encrypt } from "@/lib/crypto";
import { planFor } from "@/lib/plans";
import { createAdminClient, getProfile, requireUser } from "@/lib/supabase/server";

export async function createProject(formData: FormData): Promise<{ error?: string } | void> {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");

  const profile = await getProfile(user.id, user.email);
  const plan = planFor(profile);
  const { count } = await supabase.from("projects").select("id", { count: "exact", head: true }).is("deleted_at", null);
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

const MAX_IMPORT_BYTES = 4 * 1024 * 1024; // Vercel accepts request bodies up to 4.5 MB.

/**
 * Create a project from an uploaded manuscript in almost any format (Word, PDF, RTF, ODT, EPUB, HTML,
 * Markdown, text), split into chapters by its headings. The workspace then organizes it with AI.
 */
export async function importProject(formData: FormData): Promise<{ error?: string } | void> {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");

  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) return { error: "Choose a file to import." };
  if (file.size > MAX_IMPORT_BYTES) return { error: "That file is over 4 MB. Save it as .docx or plain text (much smaller) and try again." };
  const ext = file.name.toLowerCase().split(".").pop() ?? "";
  const { IMPORT_EXTENSIONS } = await import("@/lib/extract-text");
  if (ext !== "json" && !(IMPORT_EXTENSIONS as readonly string[]).includes(ext)) {
    return { error: "MANTIS can import Word, PDF, RTF, OpenDocument, EPUB, HTML, Markdown and text files, or a MANTIS backup (.json)." };
  }

  const profile = await getProfile(user.id, user.email);
  const plan = planFor(profile);
  const { count } = await supabase.from("projects").select("id", { count: "exact", head: true }).is("deleted_at", null);
  if ((count ?? 0) >= plan.maxProjects) {
    return { error: `The ${plan.name} plan includes ${plan.maxProjects} projects. Upgrade to import more.` };
  }

  if (ext === "json") return importBackup(await file.text(), user.id, String(formData.get("title") || "").trim());

  let text: string;
  try {
    const { extractText } = await import("@/lib/extract-text");
    text = await extractText(file);
  } catch (e) {
    console.error("Import failed to read", ext, e);
    return { error: "We couldn't read that file. Try saving it as .docx or plain text and import again." };
  }

  const { splitManuscript } = await import("@/lib/manuscript");
  const chapters = splitManuscript(text);
  const totalWords = chapters.reduce((a, c) => a + c.word_count, 0);
  if (!totalWords) {
    return {
      error: ext === "pdf" ? "That PDF has no selectable text (it may be scanned images). Export it as .docx or text and try again." : "That file doesn't seem to contain any text.",
    };
  }

  const title =
    String(formData.get("title") || "").trim().slice(0, 200) ||
    file.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim().slice(0, 200) ||
    "Imported manuscript";
  const { data: project, error } = await supabase
    .from("projects")
    .insert({ title, user_id: user.id, target_words: Math.max(80000, Math.ceil(totalWords / 10000) * 10000) })
    .select("id")
    .single();
  if (error) {
    return { error: error.message.includes("PLAN_LIMIT") ? error.message.replace(/^.*PLAN_LIMIT:\s*/, "") : error.message };
  }

  const rows = chapters.map((c, i) => ({ project_id: project.id, user_id: user.id, position: i + 1, title: c.title, content: c.content, word_count: c.word_count }));
  for (let i = 0; i < rows.length; i += 50) {
    const { error: chErr } = await supabase.from("chapters").insert(rows.slice(i, i + 50));
    if (chErr) {
      await supabase.from("projects").delete().eq("id", project.id);
      return { error: "Import failed while saving chapters. Nothing was created; please try again." };
    }
  }
  const { autoFeaturesAllowed } = await import("@/lib/plans");
  if (autoFeaturesAllowed(profile)) redirect(`/app/projects/${project.id}?organize=1`);
  if (!(profile as { organize_used?: boolean }).organize_used) {
    await createAdminClient().from("profiles").update({ organize_used: true }).eq("id", user.id);
    redirect(`/app/projects/${project.id}?organize=1`);
  }
  redirect(`/app/projects/${project.id}?organize=limit`);
}

/** Restore a MANTIS backup (.mantis.json) or an original MANTIS Studio project file. */
async function importBackup(text: string, userId: string, titleOverride: string): Promise<{ error?: string } | void> {
  const { supabase } = await requireUser();
  const { parseProjectJson } = await import("@/lib/project-import");
  let book;
  try {
    book = parseProjectJson(text);
  } catch {
    return { error: "That JSON file isn't a MANTIS project or backup." };
  }
  const { style_dials, ...fields } = book.project;
  const { data: project, error } = await supabase
    .from("projects")
    .insert({ ...fields, ...(style_dials ? { style_dials } : {}), title: titleOverride.slice(0, 200) || fields.title, user_id: userId })
    .select("id")
    .single();
  if (error) {
    return { error: error.message.includes("PLAN_LIMIT") ? error.message.replace(/^.*PLAN_LIMIT:\s*/, "") : error.message };
  }
  const fail = async () => {
    await supabase.from("projects").delete().eq("id", project.id);
    return { error: "Import failed partway through. Nothing was created; please try again." };
  };
  const chapterRows = book.chapters.map((c, i) => ({ ...c, position: i + 1, project_id: project.id, user_id: userId }));
  for (let i = 0; i < chapterRows.length; i += 50) {
    if ((await supabase.from("chapters").insert(chapterRows.slice(i, i + 50))).error) return fail();
  }
  const entityRows = book.entities.map((e) => ({ ...e, project_id: project.id, user_id: userId }));
  for (let i = 0; i < entityRows.length; i += 100) {
    if ((await supabase.from("entities").insert(entityRows.slice(i, i + 100))).error) return fail();
  }
  if (!chapterRows.length) await supabase.from("chapters").insert({ project_id: project.id, user_id: userId, position: 1, title: "Chapter 1" });
  redirect(`/app/projects/${project.id}`);
}

/** Move a book to the Trash. It can be restored for 30 days (see /app/trash). */
export async function deleteProject(projectId: string) {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  await supabase.from("projects").update({ deleted_at: new Date().toISOString() }).eq("id", projectId);
  revalidatePath("/app");
  redirect("/app?trashed=1");
}

export async function restoreProject(projectId: string): Promise<{ error?: string } | void> {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  const profile = await getProfile(user.id, user.email);
  const plan = planFor(profile);
  const { count } = await supabase.from("projects").select("id", { count: "exact", head: true }).is("deleted_at", null);
  if ((count ?? 0) >= plan.maxProjects) {
    return { error: `The ${plan.name} plan includes ${plan.maxProjects} projects. Move one to the Trash or upgrade, then restore this one.` };
  }
  const { error } = await supabase.from("projects").update({ deleted_at: null }).eq("id", projectId);
  if (error) return { error: error.message };
  revalidatePath("/app");
  redirect(`/app/projects/${projectId}`);
}

/** Permanently delete a book that is already in the Trash. */
export async function purgeProject(projectId: string): Promise<{ error?: string } | void> {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  const { error } = await supabase.from("projects").delete().eq("id", projectId).not("deleted_at", "is", null);
  if (error) return { error: error.message };
  revalidatePath("/app/trash");
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

export async function setDailyGoal(goal: number): Promise<{ error?: string; ok?: boolean }> {
  const { user } = await requireUser();
  if (!user) return { error: "Please log in." };
  const value = Math.round(Number(goal));
  if (!Number.isFinite(value) || value < 50 || value > 20000) return { error: "Pick a goal between 50 and 20,000 words." };
  await getProfile(user.id, user.email);
  const { error } = await createAdminClient().from("profiles").update({ daily_goal: value }).eq("id", user.id);
  if (error) return { error: error.message };
  revalidatePath("/app");
  return { ok: true };
}

/** One-click sample book so new writers see a filled-in workspace instead of a blank page. */
export async function createSampleProject(): Promise<{ error?: string } | void> {
  const { supabase, user } = await requireUser();
  if (!user) redirect("/login");
  const { SAMPLE } = await import("@/lib/sample-project");
  const { data: project, error } = await supabase
    .from("projects")
    .insert({ ...SAMPLE.project, user_id: user.id })
    .select("id")
    .single();
  if (error) {
    return { error: error.message.includes("PLAN_LIMIT") ? error.message.replace(/^.*PLAN_LIMIT:\s*/, "") : error.message };
  }
  await supabase.from("chapters").insert(SAMPLE.chapters.map((c, i) => ({ ...c, position: i + 1, project_id: project.id, user_id: user.id })));
  await supabase.from("entities").insert(SAMPLE.entities.map((e) => ({ ...e, project_id: project.id, user_id: user.id })));
  redirect(`/app/projects/${project.id}`);
}

/** Check the saved AI key works (original MANTIS "Check Connection"). Listing models costs nothing. */
export async function testAiKey(): Promise<{ ok: boolean; text: string }> {
  const { user } = await requireUser();
  if (!user) return { ok: false, text: "Please log in." };
  const profile = await getProfile(user.id, user.email);
  if (!profile.ai_key_encrypted) return { ok: false, text: "No key saved yet." };
  const { decrypt } = await import("@/lib/crypto");
  let key: string;
  try {
    key = decrypt(profile.ai_key_encrypted);
  } catch {
    return { ok: false, text: "The saved key couldn't be read. Please enter it again." };
  }
  const provider = (profile.ai_provider ?? "groq") as ProviderId;
  const p = PROVIDERS[provider] ?? PROVIDERS.groq;
  try {
    const res = await fetch(p.url.replace(/chat\/completions$/, "models"), { headers: { Authorization: `Bearer ${key}` }, signal: AbortSignal.timeout(10_000) });
    if (res.status === 401 || res.status === 403) return { ok: false, text: "The provider rejected this key. Check it, or create a new one." };
    if (!res.ok) return { ok: false, text: `The provider answered with an error (${res.status}). Try again in a minute.` };
    const ids: string[] = ((await res.json()).data ?? []).map((m: { id: string }) => m.id);
    const model = profile.ai_model || p.defaultModel;
    return ids.includes(model)
      ? { ok: true, text: `Key works. ${ids.length} models available, including ${model}.` }
      : { ok: true, text: `Key works (${ids.length} models). “${model}” isn't one of them, so MANTIS will pick the best available.` };
  } catch {
    return { ok: false, text: "Couldn't reach the provider. Check your connection and try again." };
  }
}
