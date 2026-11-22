import { BookMarked, Check, Sparkles } from "lucide-react";
import Link from "next/link";
import Logo from "@/components/ui/Logo";
import ThemeToggle from "@/components/ui/ThemeToggle";

const POINTS = [
  "Free forever plan with 2 projects",
  "Free AI every month, no key needed",
  "Outline, chapter editor and World Bible",
  "Export your book any time",
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="flex flex-col px-6 py-6 sm:px-10">
        <div className="flex items-center justify-between">
          <Logo />
          <ThemeToggle />
        </div>
        <div className="flex flex-1 items-center justify-center py-12">{children}</div>
        <p className="text-center text-xs text-muted">
          By continuing you agree to our{" "}
          <Link href="/legal/terms" className="underline hover:text-text">
            Terms
          </Link>{" "}
          and{" "}
          <Link href="/legal/privacy" className="underline hover:text-text">
            Privacy Policy
          </Link>
          .
        </p>
      </div>
      <aside className="relative hidden overflow-hidden border-l border-line bg-panel lg:flex lg:flex-col lg:justify-center lg:px-16">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(70%_60%_at_70%_20%,var(--accent-soft),transparent)]" />
        <div className="relative max-w-md">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-soft text-accent">
            <BookMarked size={20} />
          </span>
          <h2 className="mt-6 font-serif text-4xl leading-tight font-semibold">Your book, organized. Your canon, protected.</h2>
          <ul className="mt-8 space-y-3">
            {POINTS.map((p) => (
              <li key={p} className="flex items-center gap-3 text-sm">
                <Check size={16} className="text-accent" /> {p}
              </li>
            ))}
          </ul>
          <div className="mt-10 rounded-2xl border border-line bg-panel-2 p-5">
            <p className="flex items-center gap-2 text-xs font-semibold text-accent">
              <Sparkles size={14} /> AI that remembers your story
            </p>
            <p className="mt-2 font-serif text-sm leading-relaxed text-muted">
              Every suggestion reads your outline, canon rules and World Bible first, so your detective never forgets she&apos;s
              left-handed.
            </p>
          </div>
        </div>
      </aside>
    </div>
  );
}
