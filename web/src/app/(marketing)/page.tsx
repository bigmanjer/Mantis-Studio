import {
  ArrowRight,
  BookMarked,
  Download,
  FilePen,
  FileText,
  Library,
  ListTree,
  Lock,
  MessageCircleQuestion,
  PenLine,
  ShieldCheck,
  Sparkles,
  Upload,
  Users,
  Wand2,
} from "lucide-react";
import Link from "next/link";
import PricingTable from "@/components/billing/PricingTable";
import Comparison from "@/components/marketing/Comparison";
import EditorMock from "@/components/marketing/EditorMock";
import Faq from "@/components/marketing/Faq";
import { getOptionalUser } from "@/lib/supabase/server";

// Copy voice: one writer explaining a tool to another. Concrete problems, plain words, no hype.
const STEPS = [
  {
    icon: ListTree,
    title: "Plan",
    body: "Start with a paragraph about your story. MANTIS can sketch an outline from it, and every line becomes a chapter you can open and write.",
  },
  {
    icon: PenLine,
    title: "Write",
    body: "Write on a quiet page that saves itself. Stuck mid-scene? Ask for the next few hundred words, then keep them, rework them or throw them out.",
  },
  {
    icon: BookMarked,
    title: "Keep track",
    body: "Every name, place and rule lives in one World Bible. Before anyone else reads a chapter, run a continuity check.",
  },
];

const FEATURES = [
  {
    icon: Wand2,
    title: "AI that has actually read your book",
    body: "Most AI tools forget your story the moment you close the tab. MANTIS sends your outline, rules and characters with every request, so it won’t invent a sister you never wrote.",
    wide: true,
  },
  { icon: Users, title: "A World Bible that keeps itself", body: "As you write, MANTIS notes new characters, places and facts on its own. You can edit anything, or undo it with one click." },
  { icon: Sparkles, title: "Rewrite a passage", body: "Highlight a paragraph and ask for it tighter, darker, funnier or more vivid. Keep it or don’t." },
  {
    icon: ShieldCheck,
    title: "Continuity check",
    body: "Did her eyes change colour? Did he know about the letter yet? MANTIS reads the chapter against your notes and tells you.",
  },
  { icon: FilePen, title: "Draft from your outline", body: "Turn “Chapter 7: they get caught” into a rough first draft to push against. A starting point, not a finished page." },
  { icon: MessageCircleQuestion, title: "Ask your book", body: "“What did I call the inn in chapter two?” Ask in plain English and get the answer from your own notes." },
  { icon: Upload, title: "Bring your draft", body: "Already 40,000 words in? Upload Word, PDF, RTF, EPUB or plain text. MANTIS splits it into chapters, then builds the outline and World Bible from it." },
  {
    icon: Library,
    title: "Your research, on hand",
    body: "Drop in research notes, a series bible or a craft book you own. The AI looks things up there before it writes, and you can borrow the craft of 250 authors from Austen to Christie, never their sentences.",
  },
  { icon: FileText, title: "Focus mode", body: "Hide everything but the page. Press Esc when you want your tools back." },
  { icon: Download, title: "Take it with you", body: "Export plain text or Markdown any time. On paid plans, a formatted Word manuscript or an ebook ready for Kindle, Apple Books and Kobo." },
  {
    icon: Lock,
    title: "Your words stay yours",
    body: "Your writing is private and never used to train AI. Delete your account and it’s gone. No asterisks.",
    wide: true,
  },
];

export default async function Home() {
  const user = await getOptionalUser();
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_50%_at_50%_0%,var(--accent-soft),transparent)]" />
        <div className="relative mx-auto max-w-6xl px-4 pt-16 pb-20 text-center sm:pt-24">
          <Link
            href="/pricing"
            className="animate-fade-up inline-flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1 text-xs text-muted transition hover:text-text"
          >
            <span className="rounded-full bg-accent-soft px-2 py-0.5 font-medium text-accent">New</span>
            Try the AI free, no key needed
            <ArrowRight size={12} />
          </Link>
          <h1 className="animate-fade-up mx-auto mt-6 max-w-3xl font-serif text-4xl leading-[1.1] font-semibold tracking-tight sm:text-6xl [animation-delay:60ms]">
            Write your novel
            <br />
            <span className="text-accent">without losing the thread.</span>
          </h1>
          <p className="animate-fade-up mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted [animation-delay:120ms]">
            Your outline, your chapters and every detail of your world, in one place. And an AI helper that reads all of it before it
            says a word.
          </p>
          <div className="animate-fade-up mt-9 flex flex-col justify-center gap-3 sm:flex-row [animation-delay:180ms]">
            <Link href={user ? "/app" : "/signup"} className="btn-primary px-6 py-3 text-base">
              {user ? "Back to your books" : "Start writing, it’s free"} <ArrowRight size={16} />
            </Link>
            <Link href="#how" className="btn-ghost px-6 py-3 text-base">
              See how it works
            </Link>
          </div>
          <p className="animate-fade-up mt-4 text-xs text-muted [animation-delay:240ms]">No credit card. Your words stay yours.</p>
          <div className="animate-fade-up mt-16 [animation-delay:300ms]">
            <EditorMock />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="scroll-mt-20 border-y border-line bg-panel/40">
        <div className="mx-auto max-w-6xl px-4 py-20">
          <p className="eyebrow text-center">How it works</p>
          <h2 className="mt-3 text-center font-serif text-3xl font-semibold sm:text-4xl">From first idea to finished draft</h2>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {STEPS.map((s, i) => (
              <div key={s.title} className="relative">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
                    <s.icon size={18} />
                  </span>
                  <span className="text-xs font-semibold text-muted">STEP {i + 1}</span>
                </div>
                <h3 className="mt-4 text-lg font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-24">
        <p className="eyebrow text-center">Features</p>
        <h2 className="mt-3 text-center font-serif text-3xl font-semibold sm:text-4xl">Made for the long haul</h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-muted">
          A short story fits in your head. A novel doesn&apos;t. These are the tools for the part that doesn&apos;t.
        </p>
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div key={f.title} className={`card p-6 transition hover:border-line-strong ${f.wide ? "lg:col-span-2" : ""}`}>
              <f.icon size={20} className="text-accent" />
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Comparison */}
      <section className="mx-auto max-w-4xl px-4 pb-24">
        <p className="eyebrow text-center">Why MANTIS</p>
        <h2 className="mt-3 text-center font-serif text-3xl font-semibold sm:text-4xl">How we compare</h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-muted">
          Some writing tools make you bring your own AI key. Others sell you credits. MANTIS lets you do either, and you can try the AI
          before you pay a cent.
        </p>
        <div className="mt-10">
          <Comparison />
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="scroll-mt-20 border-y border-line bg-panel/40">
        <div className="mx-auto max-w-6xl px-4 py-24">
          <p className="eyebrow text-center">Pricing</p>
          <h2 className="mt-3 mb-10 text-center font-serif text-3xl font-semibold sm:text-4xl">Start free. Pay when it&apos;s worth it.</h2>
          <PricingTable signedIn={!!user} />
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="mx-auto max-w-3xl scroll-mt-20 px-4 py-24">
        <h2 className="mb-8 text-center font-serif text-3xl font-semibold">Good questions</h2>
        <Faq />
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-4 pb-24">
        <div className="relative overflow-hidden rounded-3xl border border-accent/30 bg-panel px-6 py-16 text-center shadow-glow">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(50%_80%_at_50%_100%,var(--accent-soft),transparent)]" />
          <div className="relative">
            <PenLine size={20} className="mx-auto text-accent" />
            <h2 className="mt-4 font-serif text-3xl font-semibold sm:text-4xl">The blank page is easier with company.</h2>
            <p className="mx-auto mt-4 max-w-xl text-muted">Two projects and free AI every month. No card, no trial clock.</p>
            <Link href={user ? "/app" : "/signup"} className="btn-primary mt-8 px-6 py-3 text-base">
              {user ? "Back to your books" : "Start your book"} <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
