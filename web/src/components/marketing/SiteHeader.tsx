import Link from "next/link";
import Logo from "@/components/ui/Logo";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { getOptionalUser } from "@/lib/supabase/server";
import MobileMenu from "./MobileMenu";
import { NAV } from "./nav";

export default async function SiteHeader() {
  const user = await getOptionalUser();
  return (
    <header className="sticky top-0 z-30 border-b border-line/70 bg-bg/75 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4">
        <Logo />
        <nav className="hidden items-center gap-1 text-sm md:flex" aria-label="Main">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} className="rounded-lg px-3 py-2 text-muted transition hover:text-text">
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          {user ? (
            <Link href="/app" className="btn-primary">
              Open Studio
            </Link>
          ) : (
            <>
              <Link href="/login" className="btn-quiet hidden sm:inline-flex">
                Log in
              </Link>
              <Link href="/signup" className="btn-primary">
                Start free
              </Link>
            </>
          )}
          <MobileMenu signedIn={!!user} />
        </div>
      </div>
    </header>
  );
}
