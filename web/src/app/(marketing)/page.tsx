import {
  ArrowRight,
  BookMarked,
  Download,
  FilePen,
  FileText,
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

const STEPS = [
  { icon: ListTree, title: "Plan", body: "Write a premise, let AI draft an outline, then turn every line into a chapter with one click." },
  { icon: PenLine, title: "Write", body: "Draft in a calm manuscript editor. When you're stuck, AI continues the scene in your voice." },
  { icon: BookMarked, title: "Keep canon", body: "Scan chapters for new characters and places, then run a continuity check to catch contradictions before readers do." },
];

const FEATURES = [
  {
    icon: Wand2,
    title: "AI that knows your book",
    body: "Every request includes your outline, canon rules, style guide, World Bible and the story so far, so suggestions stay on-story.",
    wide: true,
  },
  { icon: Users, title: "World Bible", body: "Characters, locations, items, factions and lore, searchable and always one click away." },
  { icon: Sparkles, title: "Eight rewrite styles", body: "Tighten, deepen POV, add sensory detail, make it darker or wittier — on just the passage you select." },
  { icon: ShieldCheck, title: "Continuity check", body: "One click compares a chapter against your canon rules and World Bible and lists every contradiction." },
  { icon: FilePen, title: "Draft from a beat", body: "Turn an outline line into a full first-draft chapter that picks up from the story so far." },
  { icon: MessageCircleQuestion, title: "Ask your book", body: "“Who knows about the letter?” Get answers from your own outline, canon and chapters." },
  { icon: Upload, title: "Import your draft", body: "Bring an existing Word, Markdown or text manuscript. MANTIS splits it into chapters for you." },
  { icon: FileText, title: "Focus mode", body: "Hide every panel and just write. Autosave and live word counts keep running in the background." },
  { icon: Download, title: "Export anytime", body: "Markdown and text on every plan; a formatted Word manuscript on Pro and Studio." },
  {
    icon: Lock,
    title: "Your words stay yours",
    body: "Private by default. We never sell your writing or use it to train AI. Delete your account and it's gone.",
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
            Free AI on every plan
            <ArrowRight size={12} />
          </Link>
          <h1 className="animate-fade-up mx-auto mt-6 max-w-3xl font-serif text-4xl leading-[1.1] font-semibold tracking-tight sm:text-6xl [animation-delay:60ms]">
            Write the novel.
            <br />
            <span className="text-accent">Keep the canon straight.</span>
          </h1>
          <p className="animate-fade-up mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted [animation-delay:120ms]">
            MANTIS Studio is a writing studio for long-form fiction. Outline the book, draft every chapter and track your story
            world, with an AI co-writer that actually remembers what you&apos;ve written.
          </p>
          <div className="animate-fade-up mt-9 flex flex-col justify-center gap-3 sm:flex-row [animation-delay:180ms]">
            <Link href={user ? "/app" : "/signup"} className="btn-primary px-6 py-3 text-base">
              {user ? "Open your studio" : "Start writing free"} <ArrowRight size={16} />
            </Link>
            <Link href="#how" className="btn-ghost px-6 py-3 text-base">
              See how it works
            </Link>
          </div>
          <p className="animate-fade-up mt-4 text-xs text-muted [animation-delay:240ms]">Free forever plan · AI included · No credit card</p>
          <div className="animate-fade-up mt-16 [animation-delay:300ms]">
            <EditorMock />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="scroll-mt-20 border-y border-line bg-panel/40">
        <div className="mx-auto max-w-6xl px-4 py-20">
          <p className="eyebrow text-center">How it works</p>
          <h2 className="mt-3 text-center font-serif text-3xl font-semibold sm:text-4xl">From idea to manuscript</h2>
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
        <h2 className="mt-3 text-center font-serif text-3xl font-semibold sm:text-4xl">Everything a novel needs. Nothing it doesn&apos;t.</h2>
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
        <h2 className="mt-3 text-center font-serif text-3xl font-semibold sm:text-4xl">More AI per dollar, and a real free plan</h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-muted">
          Most writing tools make you choose: bring your own AI key, or buy credits. MANTIS does both, and lets you try AI before
          you pay anything.
        </p>
        <div className="mt-10">
          <Comparison />
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="scroll-mt-20 border-y border-line bg-panel/40">
        <div className="mx-auto max-w-6xl px-4 py-24">
          <p className="eyebrow text-center">Pricing</p>
          <h2 className="mt-3 mb-10 text-center font-serif text-3xl font-semibold sm:text-4xl">Start free. Upgrade when the book needs it.</h2>
          <PricingTable signedIn={!!user} />
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="mx-auto max-w-3xl scroll-mt-20 px-4 py-24">
        <h2 className="mb-8 text-center font-serif text-3xl font-semibold">Questions, answered</h2>
        <Faq />
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-4 pb-24">
        <div className="relative overflow-hidden rounded-3xl border border-accent/30 bg-panel px-6 py-16 text-center shadow-glow">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(50%_80%_at_50%_100%,var(--accent-soft),transparent)]" />
          <div className="relative">
            <Sparkles size={20} className="mx-auto text-accent" />
            <h2 className="mt-4 font-serif text-3xl font-semibold sm:text-4xl">Your next chapter starts here</h2>
            <p className="mx-auto mt-4 max-w-xl text-muted">Free forever plan with 2 projects and free monthly AI. Upgrade or cancel any time.</p>
            <Link href={user ? "/app" : "/signup"} className="btn-primary mt-8 px-6 py-3 text-base">
              {user ? "Open your studio" : "Create your free account"} <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
