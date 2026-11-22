import Image from "next/image";
import Link from "next/link";
import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";

const FEATURES = [
  {
    title: "Outline that holds the whole book",
    body: "Lay out acts, chapter beats and your premise in one place. Turn an outline into chapters with one click.",
  },
  {
    title: "A distraction-free chapter editor",
    body: "Write in a clean manuscript view with autosave, live word counts and progress toward your target length.",
  },
  {
    title: "A World Bible that stays consistent",
    body: "Track characters, locations, items, factions and lore. Let AI pull new canon out of every chapter you write.",
  },
  {
    title: "AI that works on your draft",
    body: "Continue a scene, rewrite in eight styles, summarize chapters or brainstorm. AI knows your outline, canon rules and World Bible, so it stays on-story.",
  },
  {
    title: "Your work is saved to the cloud",
    body: "Projects sync to your account automatically, so you can write from any computer.",
  },
  {
    title: "Export when you're ready",
    body: "Download your manuscript as Markdown or plain text, or as a formatted Word document on paid plans.",
  },
];

const STEPS = [
  ["Plan", "Set your premise, then outline the chapters and their beats."],
  ["Write", "Draft chapters in the editor and let AI help where you're stuck."],
  ["Keep canon", "Build the World Bible as you go, so nothing contradicts itself."],
];

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main>
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-x-0 -top-40 h-[500px] bg-[radial-gradient(ellipse_at_center,rgba(74,222,128,0.18),transparent_60%)]" />
          <div className="relative mx-auto max-w-6xl px-4 pt-20 pb-16 text-center sm:pt-28">
            <p className="mb-4 text-xs font-medium tracking-[0.3em] text-accent uppercase">
              Modular AI Narrative Text Intelligence System
            </p>
            <h1 className="mx-auto max-w-3xl font-serif text-4xl leading-tight font-semibold sm:text-6xl">
              Write the novel. Keep the canon straight.
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-muted">
              MANTIS Studio is a writing workspace for long-form fiction. Plan, draft, track your story world and get
              AI help, all in one place.
            </p>
            <div className="mt-10 flex flex-col justify-center gap-3 sm:flex-row">
              <Link href="/signup" className="btn-primary px-6 py-3 text-base">
                Start writing free
              </Link>
              <Link href="/pricing" className="btn-ghost px-6 py-3 text-base">
                See pricing
              </Link>
            </div>
            <p className="mt-4 text-xs text-muted">Free forever plan · AI included to try · No credit card</p>
            <div className="mx-auto mt-16 max-w-4xl overflow-hidden rounded-2xl border border-line">
              <Image
                src="/mantis_banner_dark.png"
                alt="MANTIS Studio"
                width={1600}
                height={600}
                priority
                className="h-auto w-full"
              />
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16">
          <div className="grid gap-6 md:grid-cols-3">
            {STEPS.map(([title, body], i) => (
              <div key={title} className="card p-6">
                <p className="text-sm font-semibold text-accent">0{i + 1}</p>
                <h3 className="mt-2 text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted">{body}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16">
          <h2 className="text-center font-serif text-3xl font-semibold sm:text-4xl">Everything a novel needs</h2>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-6">
                <h3 className="font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-20">
          <div className="card flex flex-col items-center gap-6 p-10 text-center">
            <h2 className="font-serif text-3xl font-semibold">Your next chapter starts here</h2>
            <p className="max-w-xl text-muted">
              Start free with 2 projects and free monthly AI. Upgrade any time for unlimited projects, Word export and 1M AI tokens a month.
            </p>
            <Link href="/signup" className="btn-primary px-6 py-3 text-base">
              Create your free account
            </Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
