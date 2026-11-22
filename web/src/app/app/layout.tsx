import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getPlan } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const { user } = await requireUser();
  if (!user) redirect("/login");
  const profile = await getProfile(user.id, user.email);
  const plan = getPlan(profile.plan);

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="flex shrink-0 items-center justify-between border-b border-line bg-panel px-4 py-3 md:sticky md:top-0 md:h-screen md:w-60 md:flex-col md:items-stretch md:justify-start md:border-r md:border-b-0 md:py-6">
        <Link href="/app" className="flex items-center gap-2">
          <Image src="/mantis_favicon.png" alt="" width={28} height={28} />
          <span className="font-semibold tracking-[0.2em]">MANTIS</span>
        </Link>
        <nav className="flex items-center gap-1 text-sm md:mt-8 md:flex-col md:items-stretch">
          <Link href="/app" className="rounded-lg px-3 py-2 text-muted hover:bg-panel-2 hover:text-text">
            Projects
          </Link>
          <Link href="/app/settings" className="rounded-lg px-3 py-2 text-muted hover:bg-panel-2 hover:text-text">
            Settings & billing
          </Link>
        </nav>
        <div className="hidden md:mt-auto md:block">
          <div className="card p-3 text-xs">
            <p className="text-muted">Plan</p>
            <p className="mt-0.5 text-sm font-semibold text-accent">{plan.name}</p>
            {plan.id !== "studio" && (
              <Link href="/app/settings#plans" className="mt-2 block text-muted underline hover:text-text">
                Upgrade
              </Link>
            )}
          </div>
          <p className="mt-3 truncate text-xs text-muted" title={user.email ?? ""}>
            {user.email}
          </p>
          <form action="/auth/signout" method="post">
            <button className="mt-1 cursor-pointer text-xs text-muted hover:text-text">Sign out</button>
          </form>
        </div>
      </aside>
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
