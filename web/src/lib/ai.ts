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

export type AiAction = "continue" | "rewrite" | "summarize" | "brainstorm" | "outline" | "extract" | "custom";

export interface AiContext {
  project?: {
    title?: string;
    genre?: string;
    premise?: string;
    outline?: string;
    canon_rules?: string;
    style_guide?: string;
  };
  chapterTitle?: string;
  previousSummaries?: string[];
  entities?: { name: string; category: string; description: string }[];
}

const clip = (s: string | undefined, n: number) => (s ?? "").slice(0, n);

function projectBlock(ctx: AiContext): string {
  const p = ctx.project ?? {};
  const parts: string[] = [];
  if (p.title) parts.push(`TITLE: ${clip(p.title, 200)}`);
  if (p.genre) parts.push(`GENRE: ${clip(p.genre, 100)}`);
  if (p.premise) parts.push(`PREMISE:\n${clip(p.premise, 1500)}`);
  if (p.canon_rules) parts.push(`HARD CANON RULES (never contradict):\n${clip(p.canon_rules, 1500)}`);
  if (p.style_guide) parts.push(`STYLE GUIDE:\n${clip(p.style_guide, 1200)}`);
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
    default:
      user = `${context ? context + "\n\n" : ""}${clip(opts.instruction, 2000)}${t ? `\n\nTEXT:\n${t}` : ""}`;
  }
  return [
    { role: "system", content: SYSTEM },
    { role: "user", content: user },
  ];
}

export const PROVIDERS = {
  groq: { url: "https://api.groq.com/openai/v1/chat/completions", defaultModel: "llama-3.3-70b-versatile" },
  openai: { url: "https://api.openai.com/v1/chat/completions", defaultModel: "gpt-4o-mini" },
} as const;

export type ProviderId = keyof typeof PROVIDERS;

export async function callModel(opts: {
  provider: ProviderId;
  apiKey: string;
  model?: string | null;
  messages: { role: string; content: string }[];
  maxTokens?: number;
}): Promise<{ text: string; tokens: number }> {
  const p = PROVIDERS[opts.provider];
  const res = await fetch(p.url, {
    method: "POST",
    headers: { Authorization: `Bearer ${opts.apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: opts.model || p.defaultModel,
      messages: opts.messages,
      temperature: 0.8,
      max_tokens: opts.maxTokens ?? 1500,
    }),
    signal: AbortSignal.timeout(60_000),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    if (res.status === 401) throw new AiError("The AI provider rejected the API key.", 400);
    if (res.status === 429) throw new AiError("The AI provider is rate-limiting requests. Try again in a minute.", 429);
    throw new AiError(`AI provider error (${res.status}). ${body.slice(0, 200)}`, 502);
  }
  const data = await res.json();
  const text: string = data.choices?.[0]?.message?.content ?? "";
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
