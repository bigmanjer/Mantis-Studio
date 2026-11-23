"use client";

export interface AiRequest {
  action: "continue" | "rewrite" | "summarize" | "brainstorm" | "outline" | "extract" | "draft" | "check" | "ask" | "autofill" | "custom";
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
