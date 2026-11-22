import { ChevronDown } from "lucide-react";

export const FAQ: [string, string][] = [
  [
    "Do I need to know anything about AI?",
    "Nope. Every account gets some free AI each month with nothing to set up. If you write a lot, Studio includes a million tokens a month. Bringing your own key is optional.",
  ],
  [
    "What does “bring your own key” mean?",
    "You can paste an API key from Groq (which has a free tier) or OpenAI into Settings. AI requests then bill to that account instead of using your monthly allowance. Your key is encrypted before it's stored.",
  ],
  [
    "Is my writing private? Will you train AI on it?",
    "Your projects are visible to your account and nobody else. We don’t sell your writing and we don’t train AI on it. When you use an AI feature, only the text that request needs is sent to the AI provider.",
  ],
  [
    "What happens on Studio when I use up the included AI?",
    "If you've saved your own key, MANTIS switches to it automatically. Otherwise AI pauses until your allowance resets next month. Writing, planning and export keep working either way.",
  ],
  ["Can I cancel any time?", "Yes. Manage or cancel from Settings in two clicks. You keep your plan until the end of the period you paid for."],
  [
    "What happens to my projects if I downgrade?",
    "Nothing is deleted. On Free you can still open, edit and export everything; you just can't create new projects beyond the limit.",
  ],
  ["Can I take my book elsewhere?", "Any time, on any plan. Download plain text or Markdown, or a formatted Word manuscript on Pro and Studio. It’s your book."],
];

export default function Faq({ items = FAQ }: { items?: [string, string][] }) {
  return (
    <div className="divide-y divide-line rounded-2xl border border-line bg-panel">
      {items.map(([q, a]) => (
        <details key={q} className="group px-5 py-4 [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium">
            {q}
            <ChevronDown size={18} className="shrink-0 text-muted transition group-open:rotate-180" />
          </summary>
          <p className="mt-3 text-sm leading-relaxed text-muted">{a}</p>
        </details>
      ))}
    </div>
  );
}
