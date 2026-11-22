import Image from "next/image";
import Link from "next/link";
import { getOptionalUser } from "@/lib/supabase/server";

export default async function SiteHeader() {
  const user = await getOptionalUser();
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-bg/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/mantis_favicon.png" alt="" width={32} height={32} />
          <span className="text-lg font-semibold tracking-[0.2em]">MANTIS</span>
        </Link>
        <nav className="flex items-center gap-3 text-sm sm:gap-5">
          <Link href="/#features" className="hidden text-muted hover:text-text sm:inline">
            Features
          </Link>
          <Link href="/pricing" className="text-muted hover:text-text">
            Pricing
          </Link>
          {user ? (
            <Link href="/app" className="btn-primary">
              Open Studio
            </Link>
          ) : (
            <>
              <Link href="/login" className="text-muted hover:text-text">
                Log in
              </Link>
              <Link href="/signup" className="btn-primary">
                Start free
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
