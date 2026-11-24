"use client";
import { cleanPartial, stripMarkdown } from "@/lib/text-clean";

export interface AiRequest {
  action: "continue" | "rewrite" | "summarize" | "brainstorm" | "outline" | "extract" | "draft" | "check" | "ask" | "autofill" | "reverse_outline" | "enrich" | "review" | "custom";
  text?: string;
  preset?: string;
  instruction?: string;
  words?: number;
  context?: unknown;
}

export class AiClientError extends Error {
  constructor(
    message: string,
    public needsKey = false,
  ) {
    super(message);
  }
}

export async function runAi(req: AiRequest): Promise<string> {
  const res = await fetch("/api/ai", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new AiClientError(data.error ?? "AI request failed.", !!data.needsKey);
  return data.text as string;
}

/**
 * Like runAi, but shows the answer as the AI writes it. `onText` gets the cleaned text so far.
 * Resolves with the finished, cleaned text.
 */
export async function streamAi(req: AiRequest, onText: (text: string) => void): Promise<string> {
  const res = await fetch("/api/ai", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...req, stream: true }),
  });
  const type = res.headers.get("content-type") ?? "";
  if (!res.ok || type.includes("application/json")) {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new AiClientError(data.error ?? "AI request failed.", !!data.needsKey);
    onText(data.text ?? "");
    return data.text as string;
  }
  if (!res.body) throw new AiClientError("AI request failed.");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let raw = "";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      raw += decoder.decode(value, { stream: true });
      onText(cleanPartial(raw));
    }
  } catch {
    if (!raw.trim()) throw new AiClientError("The connection dropped. Please try again.");
  }
  const text = stripMarkdown(raw);
  if (!text) throw new AiClientError("The AI came back empty. Please try again.");
  onText(text);
  return text;
}
