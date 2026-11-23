import "server-only";

export const REWRITE_PRESETS: Record<string, string> = {
  "Fix Grammar": "Correct grammar and spelling only. Change nothing else.",
  "Improve Flow": "Fix awkward phrasing and sentence rhythm while keeping the meaning and voice.",
  "Sensory Expansion": "Show, don't tell. Add smells, sounds, textures and concrete detail.",
  "Deepen POV": "Add more internal monologue and emotional reaction from the point-of-view character.",
  "Make Witty": "Add humor, banter and irony without changing what happens.",
  "Make Darker": "Make the descriptions grim, moody and noir-styled.",
  Tighten: "Cut filler and redundancy. Aim for about 20% shorter.",
  Expand: "Add more detail and texture; roughly double the length.",
};

export type AiAction = "continue" | "rewrite" | "summarize" | "brainstorm" | "outline" | "extract" | "draft" | "check" | "ask" | "autofill" | "reverse_outline" | "enrich" | "custom";

export interface AiContext {
  project?: {
    title?: string;
    genre?: string;
    premise?: string;
    outline?: string;
    canon_rules?: string;
    style_guide?: string;
    style_dials?: Record<string, number> | null;
  };
  chapterTitle?: string;
  previousSummaries?: string[];
  entities?: { name: string; category: string; description: string }[];
}

const clip = (s: string | undefined, n: number) => (s ?? "").slice(0, n);

// Style dials: 0-100 sliders from the original MANTIS "Author & Style Lab" craft controls.
export const STYLE_DIALS = [
  { key: "pace", label: "Pace", low: "slow and lingering", high: "fast and propulsive" },
  { key: "interiority", label: "Interiority", low: "external, show through action", high: "deep inside the character's head" },
  { key: "imagery", label: "Imagery", low: "plain and spare", high: "rich, lyrical and sensory" },
  { key: "dialogue", label: "Dialogue", low: "mostly narration", high: "dialogue-driven" },
  { key: "mood", label: "Mood", low: "light and warm", high: "dark and tense" },
] as const;

function describeDials(d: Record<string, number> | null | undefined): string {
  if (!d) return "";
  return STYLE_DIALS.filter((x) => typeof d[x.key] === "number" && Math.abs(d[x.key] - 50) >= 10)
    .map((x) => {
      const v = d[x.key];
      const strength = Math.abs(v - 50) >= 35 ? "strongly" : "somewhat";
      return `- ${x.label}: ${strength} ${v > 50 ? x.high : x.low}`;
    })
    .join("\n");
}

function projectBlock(ctx: AiContext): string {
  const p = ctx.project ?? {};
  const parts: string[] = [];
  if (p.title) parts.push(`TITLE: ${clip(p.title, 200)}`);
  if (p.genre) parts.push(`GENRE: ${clip(p.genre, 100)}`);
  if (p.premise) parts.push(`PREMISE:\n${clip(p.premise, 1500)}`);
  if (p.canon_rules) parts.push(`HARD CANON RULES (never contradict):\n${clip(p.canon_rules, 1500)}`);
  if (p.style_guide) parts.push(`STYLE GUIDE:\n${clip(p.style_guide, 1200)}`);
  const dials = describeDials(p.style_dials);
  if (dials) parts.push(`STYLE DIALS (apply to anything you write):\n${dials}`);
  if (p.outline) parts.push(`OUTLINE:\n${clip(p.outline, 3000)}`);
  if (ctx.previousSummaries?.length)
    parts.push(`STORY SO FAR:\n${ctx.previousSummaries.slice(-5).map((s) => `- ${clip(s, 400)}`).join("\n")}`);
  if (ctx.entities?.length)
    parts.push(
      `WORLD BIBLE:\n${ctx.entities
        .slice(0, 40)
        .map((e) => `- ${e.name} (${e.category}): ${clip(e.description, 200)}`)
        .join("\n")}`,
    );
  return parts.join("\n\n");
}

const SYSTEM =
  "You are MANTIS, an expert fiction editor and co-writer. Respect the author's voice, the established canon and the World Bible. Output only the requested text — no preambles, no commentary, no markdown headings unless asked.";

export function buildMessages(
  action: AiAction,
  text: string,
  ctx: AiContext,
  opts: { preset?: string; instruction?: string; words?: number },
): { role: "system" | "user"; content: string }[] {
  const context = projectBlock(ctx);
  const t = clip(text, 24000);
  let user: string;
  switch (action) {
    case "continue":
      user = `${context}\n\nCURRENT CHAPTER: ${clip(ctx.chapterTitle, 200)}\n\nTEXT SO FAR (ends mid-chapter):\n${t.slice(-8000)}\n\nContinue the chapter seamlessly from where it stops, for about ${opts.words ?? 400} words. Match tense, POV and voice. ${opts.instruction ? `Author direction: ${clip(opts.instruction, 600)}` : ""}`;
      break;
    case "rewrite": {
      const instr = opts.preset && REWRITE_PRESETS[opts.preset] ? REWRITE_PRESETS[opts.preset] : clip(opts.instruction, 1000);
      user = `${context ? context + "\n\n" : ""}Rewrite the passage below.\nINSTRUCTION: ${instr || "Improve it."}\n\nPASSAGE:\n${t}`;
      break;
    }
    case "summarize":
      user = `Summarize this chapter in 3-5 sentences for a story-so-far log. Focus on plot events, character changes and revealed facts.\n\nCHAPTER:\n${t}`;
      break;
    case "brainstorm":
      user = `${context}\n\nBrainstorm for the author. Give 5 distinct, specific ideas as a numbered list.\nREQUEST: ${clip(opts.instruction, 1000) || "What could happen next?"}${t ? `\n\nCURRENT TEXT:\n${t.slice(-4000)}` : ""}`;
      break;
    case "outline":
      user = `${context}\n\nWrite a chapter-by-chapter outline for this novel. Use exactly this format, one line per chapter:\nChapter 1: <title> — <2-3 sentence beat>\nAim for ${opts.words ?? 20} chapters with a clear three-act structure.${opts.instruction ? `\nAuthor direction: ${clip(opts.instruction, 600)}` : ""}`;
      break;
    case "extract":
      user = `Extract story-world canon from the chapter below. Return ONLY a JSON array, no other text. Each item: {"name": string, "category": "Character"|"Location"|"Item"|"Faction"|"Lore", "description": string (1-2 sentences of facts stated in the text)}. Include only named, story-relevant entities. Maximum 20 items.\n\nCHAPTER:\n${t}`;
      break;
    case "draft":
      // Sudowrite-style "write the chapter from its beat".
      user = `${context}\n\nCHAPTER TO WRITE: ${clip(ctx.chapterTitle, 200)}\nBEAT (what must happen): ${clip(opts.instruction, 1500)}\n${t.trim() ? `\nEXISTING OPENING (continue from here, don't repeat it):\n${t.slice(-4000)}\n` : ""}\nWrite this chapter as finished prose, about ${opts.words ?? 1200} words. Follow the style guide and canon rules, pick up naturally from the story so far, and end on a moment that pulls the reader into the next chapter.`;
      break;
    case "check":
      // Continuity check: compare the chapter against canon rules, the World Bible and earlier summaries.
      user = `${context}\n\nYou are a meticulous continuity editor. Compare the CHAPTER below against the hard canon rules, the World Bible and the story so far. Find contradictions or likely continuity errors (names, ages, timeline, places, who-knows-what, physical details, magic/tech rules). Do not comment on style.\nReturn ONLY a JSON array, no other text. Each item: {"problem": short explanation, "quote": the exact sentence or phrase from the chapter, copied character-for-character, "canon": what canon says, "fix": replacement text for the quote that resolves the problem}. Return [] if there are no issues. Maximum 10 items.\n\nCHAPTER:\n${t}`;
      break;
    case "reverse_outline":
      // Outline from existing chapters (original MANTIS "reverse engineer outline").
      user = `${context}\n\nCHAPTERS (title and opening or summary):\n${t.slice(0, 20000)}\n\nWrite an outline of the book as it exists, one line per chapter in exactly this format:\nChapter 1: <title> \u2014 <2-3 sentence beat describing what happens>\nThen, under a line "Next:", suggest 3 possible next chapters in the same format.`;
      break;
    case "enrich":
      // Expand a World Bible entry (original MANTIS "enrich entity").
      user = `${context}\n\nENTRY TO EXPAND: ${clip(opts.instruction, 300)}\nCURRENT NOTES:\n${t.slice(0, 4000) || "(none)"}\n\nExpand these notes into a richer World Bible entry as short bullet points (appearance, history, motivations or function, relationships, secrets or open questions). Keep everything consistent with the canon and existing notes, keep facts already stated, and mark any new invention with "(idea)". Return only the bullet points.`;
      break;
    case "ask":
      // Q&A about the author's own book.
      user = `${context}\n\n${t.trim() ? `CURRENT CHAPTER (${clip(ctx.chapterTitle, 120)}):\n${t.slice(-6000)}\n\n` : ""}The author asks about their own book. Answer from the material above only. If the answer isn't established yet, say so and offer 2-3 options that would fit the canon. Be concise.\n\nQUESTION: ${clip(opts.instruction, 1000)}`;
      break;
    case "autofill":
      // Fill in a project's planning fields from whatever the author already has.
      user = `${context}\n\n${t.trim() ? `SAMPLE OF THE MANUSCRIPT:\n${t.slice(0, 6000)}\n\n` : ""}${opts.instruction ? `AUTHOR NOTES: ${clip(opts.instruction, 600)}\n\n` : ""}Based only on the material above, propose planning details for this novel. Return ONLY a JSON object, no other text, with these string fields:
{"title": a compelling working title (max 8 words),
 "genre": a short genre label like "Fantasy" or "Psychological thriller",
 "premise": 2-3 sentences: who the protagonist is, what they want, and what stands in the way,
 "canon_rules": 3-6 short facts the story must never contradict (ages, rules of the world, timeline), one per line,
 "style_guide": 1-2 sentences describing POV, tense, voice and tone as they appear in the writing}
Where the material already states something, keep it consistent with that.`;
      break;
    default:
      user = `${context ? context + "\n\n" : ""}${clip(opts.instruction, 2000)}${t ? `\n\nTEXT:\n${t}` : ""}`;
  }
  return [
    { role: "system", content: SYSTEM },
    { role: "user", content: user },
  ];
}

export const PROVIDERS = {
  groq: { url: "https://api.groq.com/openai/v1/chat/completions", defaultModel: "openai/gpt-oss-120b" },
  openai: { url: "https://api.openai.com/v1/chat/completions", defaultModel: "gpt-4o-mini" },
  // Vercel AI Gateway (OpenAI-compatible). Used for the AI included in plans when no Groq key is set.
  gateway: { url: "https://ai-gateway.vercel.sh/v1/chat/completions", defaultModel: "google/gemini-2.5-flash-lite" },
} as const;

export type ProviderId = keyof typeof PROVIDERS;

// Providers retire models without notice. If the configured model is gone, we look up what the key
// can use and pick the best text model, so the app keeps working instead of failing for every writer.
const MODEL_PREFERENCE = [/gpt-oss-120b/, /llama-4-maverick/, /llama-3\.3-70b/, /70b/, /qwen3?-32b/, /gpt-oss-20b/, /llama-4-scout/, /gpt-4o-mini/, /gpt-4\.1-mini/];
const fallbackModels = new Map<string, string>();

async function pickAvailableModel(provider: ProviderId, apiKey: string): Promise<string | null> {
  const cacheKey = `${provider}:${apiKey.slice(-6)}`;
  const cached = fallbackModels.get(cacheKey);
  if (cached) return cached;
  try {
    const res = await fetch(PROVIDERS[provider].url.replace(/chat\/completions$/, "models"), {
      headers: { Authorization: `Bearer ${apiKey}` },
      signal: AbortSignal.timeout(10_000),
    });
    if (!res.ok) return null;
    const ids: string[] = ((await res.json()).data ?? []).map((m: { id: string }) => m.id);
    const usable = ids.filter((id) => !/whisper|guard|tts|embed|vision|audio|orpheus|prompt|compound|image|dall|moderation/i.test(id));
    for (const re of MODEL_PREFERENCE) {
      const hit = usable.find((id) => re.test(id));
      if (hit) {
        fallbackModels.set(cacheKey, hit);
        return hit;
      }
    }
    if (usable[0]) fallbackModels.set(cacheKey, usable[0]);
    return usable[0] ?? null;
  } catch {
    return null;
  }
}

export async function callModel(opts: {
  provider: ProviderId;
  apiKey: string;
  model?: string | null;
  messages: { role: string; content: string }[];
  maxTokens?: number;
}): Promise<{ text: string; tokens: number }> {
  const p = PROVIDERS[opts.provider];
  const send = (model: string) =>
    fetch(p.url, {
      method: "POST",
      headers: { Authorization: `Bearer ${opts.apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages: opts.messages,
        temperature: 0.8,
        max_tokens: opts.maxTokens ?? 1500,
      }),
      signal: AbortSignal.timeout(60_000),
    });
  const cacheKey = `${opts.provider}:${opts.apiKey.slice(-6)}`;
  let model = fallbackModels.get(cacheKey) || opts.model || p.defaultModel;
  let res = await send(model);
  let body = "";
  if (!res.ok) {
    body = await res.text().catch(() => "");
    if ((res.status === 404 || res.status === 400) && /model_not_found|decommissioned|does not exist|not supported/i.test(body)) {
      const alt = await pickAvailableModel(opts.provider, opts.apiKey);
      if (alt && alt !== model) {
        console.warn(`AI provider ${opts.provider}: model ${model} unavailable, using ${alt}`);
        model = alt;
        res = await send(model);
        body = res.ok ? "" : await res.text().catch(() => "");
      }
    }
  }
  if (!res.ok) {
    // Full details go to the server log only; writers get a plain, safe message.
    console.error(`AI provider ${opts.provider} returned ${res.status}: ${body.slice(0, 500)}`);
    if (res.status === 429) throw new AiError("The AI is busy right now. Please try again in a minute.", 429);
    if (opts.provider === "gateway") {
      throw new AiError("The built-in AI isn't available right now. Please try again later, or add your own AI key in Settings.", 503);
    }
    if (res.status === 401 || res.status === 403) {
      throw new AiError("Your AI key was rejected. Please check it in Settings.", 400);
    }
    throw new AiError("The AI couldn't respond just now. Please try again.", 502);
  }
  const data = await res.json();
  let text: string = data.choices?.[0]?.message?.content ?? "";
  // Some reasoning models wrap their thinking in <think> tags; writers only want the answer.
  text = text.replace(/<think>[\s\S]*?<\/think>/g, "");
  const tokens: number = data.usage?.total_tokens ?? Math.ceil(JSON.stringify(opts.messages).length / 4 + text.length / 4);
  return { text: text.trim(), tokens };
}

export class AiError extends Error {
  constructor(
    message: string,
    public status = 400,
  ) {
    super(message);
  }
}
