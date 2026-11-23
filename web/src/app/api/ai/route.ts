import { NextResponse } from "next/server";
import { AiError, buildMessages, callModel, type AiAction, type AiContext, type ProviderId } from "@/lib/ai";
import { decrypt } from "@/lib/crypto";
import { currentPeriod, planFor } from "@/lib/plans";
import { createAdminClient, getProfile, requireUser } from "@/lib/supabase/server";
import { includedAiCredentials } from "@/lib/env";

const ACTIONS: AiAction[] = ["continue", "rewrite", "summarize", "brainstorm", "outline", "extract", "draft", "check", "ask", "autofill", "reverse_outline", "enrich", "custom"];

export async function POST(req: Request) {
  const { user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Please log in." }, { status: 401 });

  const body = await req.json().catch(() => null);
  const action = body?.action as AiAction;
  if (!ACTIONS.includes(action)) return NextResponse.json({ error: "Unknown AI action." }, { status: 400 });

  const profile = await getProfile(user.id, user.email);
  const plan = planFor(profile);
  const admin = createAdminClient();
  const period = currentPeriod();

  // Decide whose key pays. Studio draws on its included allowance first (that's what they pay for);
  // Free/Pro use their own key when they have one and only fall back to the small included allowance.
  let provider: ProviderId = profile.ai_provider ?? "groq";
  let apiKey: string | null = null;
  let model = profile.ai_model;
  let usingIncluded = false;

  const tryOwnKey = (): NextResponse | null => {
    if (apiKey || !plan.byokAi || !profile.ai_key_encrypted) return null;
    try {
      apiKey = decrypt(profile.ai_key_encrypted);
    } catch {
      return NextResponse.json({ error: "Your saved AI key couldn't be read. Please re-enter it in Settings." }, { status: 400 });
    }
    return null;
  };
  const tryIncluded = async () => {
    if (apiKey || plan.includedAiTokens <= 0) return;
    const creds = await includedAiCredentials();
    if (!creds) return;
    const { data: usage } = await admin.from("ai_usage").select("tokens").eq("user_id", user.id).eq("period", period).maybeSingle();
    if ((usage?.tokens ?? 0) < plan.includedAiTokens) {
      provider = creds.provider;
      apiKey = creds.apiKey;
      model = creds.model;
      usingIncluded = true;
    }
  };

  if (plan.id === "studio") {
    await tryIncluded();
    const err = tryOwnKey();
    if (err) return err;
  } else {
    const err = tryOwnKey();
    if (err) return err;
    await tryIncluded();
  }
  if (!apiKey) {
    const msg =
      plan.id === "studio"
        ? "You've used this month's included AI. Add your own key in Settings to keep going, or wait for next month."
        : "You've used this month's free AI. Add your own Groq or OpenAI key in Settings for unlimited AI, or upgrade to Studio for 1M tokens a month.";
    return NextResponse.json({ error: msg, needsKey: true }, { status: 402 });
  }

  try {
    const messages = buildMessages(action, String(body.text ?? ""), (body.context ?? {}) as AiContext, {
      preset: body.preset,
      instruction: body.instruction,
      words: typeof body.words === "number" ? Math.min(Math.max(body.words, 50), 2000) : undefined,
    });
    const wordsReq = Math.min(Math.max(Number(body.words) || (action === "draft" ? 1200 : 400), 50), 2000);
    const maxTokens = action === "continue" || action === "draft" ? Math.ceil(wordsReq * 2) : action === "outline" || action === "reverse_outline" ? 3000 : 2000;
    const result = await callModel({ provider, apiKey, model, messages, maxTokens });
    if (usingIncluded) {
      await admin.rpc("add_ai_usage", { p_user: user.id, p_period: period, p_tokens: result.tokens });
    }
    return NextResponse.json({ text: result.text, tokens: result.tokens, included: usingIncluded });
  } catch (e) {
    const err = e instanceof AiError ? e : new AiError("The AI request failed. Please try again.", 502);
    return NextResponse.json({ error: err.message }, { status: err.status });
  }
}
