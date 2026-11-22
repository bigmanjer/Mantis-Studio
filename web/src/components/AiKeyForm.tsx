"use client";
import { useState, useTransition } from "react";
import { saveAiSettings } from "@/app/app/actions";

export default function AiKeyForm({ provider, model, maskedKey }: { provider: string; model: string; maskedKey: string | null }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [prov, setProv] = useState(provider);

  function submit(fd: FormData) {
    start(async () => {
      const res = await saveAiSettings(fd);
      setMsg(res.error ? { ok: false, text: res.error } : { ok: true, text: "Saved." });
    });
  }

  return (
    <form action={submit} className="mt-5 grid gap-4 sm:grid-cols-[160px_1fr_200px]">
      <div>
        <label className="label">Provider</label>
        <select name="provider" className="input" value={prov} onChange={(e) => setProv(e.target.value)}>
          <option value="groq">Groq</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      <div>
        <label className="label">API key {maskedKey && <span className="normal-case">(saved: {maskedKey})</span>}</label>
        <input
          name="apiKey"
          type="password"
          autoComplete="off"
          className="input"
          placeholder={maskedKey ? "Leave blank to keep the saved key" : prov === "groq" ? "gsk_…" : "sk-…"}
        />
      </div>
      <div>
        <label className="label">Model (optional)</label>
        <input name="model" className="input" defaultValue={model} placeholder={prov === "groq" ? "llama-3.3-70b-versatile" : "gpt-4o-mini"} />
      </div>
      <div className="flex flex-wrap items-center gap-3 sm:col-span-3">
        <button type="submit" disabled={pending} className="btn-primary">
          {pending ? "Saving…" : "Save AI settings"}
        </button>
        {maskedKey && (
          <button type="submit" name="clear" value="1" disabled={pending} className="btn-ghost">
            Remove saved key
          </button>
        )}
        {msg && <span className={`text-sm ${msg.ok ? "text-accent" : "text-danger"}`}>{msg.text}</span>}
      </div>
    </form>
  );
}
