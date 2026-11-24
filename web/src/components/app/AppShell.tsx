"use client";
import { CreditCard, FolderOpen, LogOut, Menu, Settings, ShieldCheck, Sparkles, Trash2, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ConfirmProvider } from "@/components/ui/ConfirmDialog";
import Logo from "@/components/ui/Logo";
import { ProgressBar } from "@/components/ui/Progress";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { compact } from "@/lib/format";

export interface ShellUser {
  email: string;
  planId: "free" | "pro" | "studio";
  planName: string;
  aiUsed: number;
  aiLimit: number;
  isAdmin?: boolean;
}

const ADMIN_NAV = { href: "/app/admin", label: "Admin", icon: ShieldCheck, match: (p: string) => p === "/app/admin" };

const NAV = [
  { href: "/app", label: "Projects", icon: FolderOpen, match: (p: string) => p === "/app" || p.startsWith("/app/projects") },
  { href: "/app/trash", label: "Trash", icon: Trash2, match: (p: string) => p === "/app/trash" },
  { href: "/app/settings", label: "Settings", icon: Settings, match: (p: string) => p === "/app/settings" },
  { href: "/app/settings#billing", label: "Plan & billing", icon: CreditCard, match: () => false },
];

function SidebarBody({ user, pathname, onNavigate }: { user: ShellUser; pathname: string; onNavigate?: () => void }) {
  const pct = user.aiLimit ? (user.aiUsed / user.aiLimit) * 100 : 0;
  return (
    <div className="flex h-full flex-col">
      <div className="px-2">
        <Logo href="/app" />
      </div>
      <nav className="mt-8 space-y-0.5" aria-label="App">
        {[...NAV, ...(user.isAdmin ? [ADMIN_NAV] : [])].map((n) => {
          const active = n.match(pathname);
          return (
            <Link
              key={n.label}
              href={n.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                active ? "bg-panel-3 font-medium text-text" : "text-muted hover:bg-panel-2 hover:text-text"
              }`}
            >
              <n.icon size={16} className={active ? "text-accent" : ""} />
              {n.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto space-y-3">
        <div className="rounded-xl border border-line bg-panel-2 p-3.5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted">Plan</span>
            <span className="text-xs font-semibold text-accent">{user.planName}</span>
          </div>
          {user.aiLimit > 0 && (
            <>
              <div className="mt-3 flex items-center justify-between text-[11px] text-muted">
                <span className="flex items-center gap-1">
                  <Sparkles size={11} /> AI this month
                </span>
                <span>
                  {compact(user.aiUsed)} / {compact(user.aiLimit)}
                </span>
              </div>
              <ProgressBar value={pct} className="mt-1.5" />
            </>
          )}
          {user.planId !== "studio" && !user.isAdmin && (
            <Link href="/app/settings#billing" onClick={onNavigate} className="btn-primary mt-3 w-full py-1.5 text-xs">
              Upgrade
            </Link>
          )}
        </div>
        <div className="border-t border-line pt-3">
          <p className="truncate px-3 text-xs text-muted" title={user.email}>
            {user.email}
          </p>
          <div className="mt-1">
            <ThemeToggle withLabel />
          </div>
          <form action="/auth/signout" method="post">
            <button className="btn-quiet w-full justify-start px-3">
              <LogOut size={16} /> Sign out
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function AppShell({ user, children }: { user: ShellUser; children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [pathname]);

  // An open book gets the whole screen; the workspace has its own header with a way back.
  if (pathname.startsWith("/app/projects/")) {
    return <ConfirmProvider>{children}</ConfirmProvider>;
  }

  return (
    <ConfirmProvider>
      <div className="flex min-h-screen">
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-line bg-panel px-3 py-5 lg:block">
          <SidebarBody user={user} pathname={pathname} />
        </aside>

        {/* Mobile top bar + drawer */}
        <div className="fixed inset-x-0 top-0 z-30 flex h-14 items-center justify-between border-b border-line bg-panel/90 px-4 backdrop-blur lg:hidden">
          <Logo href="/app" />
          <button onClick={() => setOpen(true)} className="btn-quiet h-9 w-9 p-0" aria-label="Open menu">
            <Menu size={18} />
          </button>
        </div>
        {open && (
          <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
            <button className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} aria-label="Close menu" />
            <aside className="absolute inset-y-0 left-0 w-72 border-r border-line bg-panel px-3 py-5 shadow-soft">
              <button onClick={() => setOpen(false)} className="btn-quiet absolute top-4 right-3 h-9 w-9 p-0" aria-label="Close menu">
                <X size={18} />
              </button>
              <SidebarBody user={user} pathname={pathname} onNavigate={() => setOpen(false)} />
            </aside>
          </div>
        )}

        <main className="min-w-0 flex-1 pt-14 lg:pt-0">{children}</main>
      </div>
    </ConfirmProvider>
  );
}
