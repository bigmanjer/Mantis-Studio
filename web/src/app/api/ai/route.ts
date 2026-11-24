import { NextResponse } from "next/server";
import { AiError, buildMessages, callModel, streamModel, stripMarkdown, type AiAction, type AiContext, type ProviderId } from "@/lib/ai";
import { decrypt } from "@/lib/crypto";
import { currentPeriod, planFor } from "@/lib/plans";
import { createAdminClient, getProfile, requireUser } from "@/lib/supabase/server";
import { includedAiCredentials } from "@/lib/env";

const ACTIONS: AiAction[] = ["continue", "rewrite", "summarize", "brainstorm", "outline", "extract", "draft", "check", "ask", "autofill", "reverse_outline", "enrich", "custom"];
const KNOWLEDGE_ACTIONS: AiAction[] = ["continue", "rewrite", "brainstorm", "draft", "ask", "custom", "enrich", "outline"];
const STREAMABLE: AiAction[] = ["continue", "rewrite", "brainstorm", "draft", "ask", "custom", "enrich", "summarize"];
// Streaming answers can run longer than the default function limit on slow models.
export const maxDuration = 60;

export async function POST(req: Request) {
  const { supabase, user } = await requireUser();
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
    const ctx = (body.context ?? {}) as AiContext;
    delete ctx.knowledge; // only ever set here on the server
    // Knowledge Base: the few reference passages and style lenses that matter for this request.
    if (KNOWLEDGE_ACTIONS.includes(action) && ctx.project) {
      const { knowledgeBlock } = await import("@/lib/knowledge");
      const text = String(body.text ?? "");
      ctx.knowledge = await knowledgeBlock(supabase, {
        projectId: typeof ctx.project.id === "string" ? ctx.project.id : null,
        query: [body.instruction, ctx.chapterTitle, ctx.project.genre, text.slice(-1200)].filter(Boolean).join("\n"),
        lenses: Array.isArray(ctx.project.style_lenses) ? ctx.project.style_lenses.slice(0, 3).map(String) : [],
        useLibrary: ctx.project.use_knowledge !== false,
      }).catch(() => "");
    }
    const messages = buildMessages(action, String(body.text ?? ""), ctx, {
      preset: body.preset,
      instruction: body.instruction,
      // For outlines "words" is the chapter count, so it must not be clamped like a word count.
      words:
        typeof body.words !== "number"
          ? undefined
          : action === "outline"
            ? Math.min(Math.max(Math.round(body.words), 1), 80)
            : Math.min(Math.max(body.words, 50), 2000),
    });
    const wordsReq = Math.min(Math.max(Number(body.words) || (action === "draft" ? 1200 : 400), 50), 2000);
    const maxTokens = action === "continue" || action === "draft" ? Math.ceil(wordsReq * 2) : action === "outline" ? Math.min(800 + (Number(body.words) || 20) * 110, 9000) : action === "reverse_outline" ? 3000 : 2000;
    const logUsage = async (tokens: number) => {
      if (usingIncluded) await admin.rpc("add_ai_usage", { p_user: user.id, p_period: period, p_tokens: tokens });
    };

    // Prose answers stream word by word so writers see the AI writing instead of a spinner.
    if (body.stream === true && STREAMABLE.includes(action)) {
      const stream = await streamModel({ provider, apiKey, model, messages, maxTokens }, (tokens) => logUsage(tokens));
      return new Response(stream, {
        headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store", "X-Accel-Buffering": "no" },
      });
    }

    const result = await callModel({ provider, apiKey, model, messages, maxTokens });
    if (usingIncluded) {
      await admin.rpc("add_ai_usage", { p_user: user.id, p_period: period, p_tokens: result.tokens });
    }
    const JSON_ACTIONS: AiAction[] = ["extract", "check", "autofill"];
    const text = JSON_ACTIONS.includes(action) ? result.text : stripMarkdown(result.text);
    return NextResponse.json({ text, tokens: result.tokens, included: usingIncluded });
  } catch (e) {
    const err = e instanceof AiError ? e : new AiError("The AI request failed. Please try again.", 502);
    return NextResponse.json({ error: err.message }, { status: err.status });
  }
}
