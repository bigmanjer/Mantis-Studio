import { BookOpen, Feather, Sparkles, Users } from "lucide-react";
import { notFound } from "next/navigation";
import Badge from "@/components/ui/Badge";
import { compact, timeAgo } from "@/lib/format";
import { currentPeriod } from "@/lib/plans";
import { createAdminClient, getProfile, requireUser } from "@/lib/supabase/server";

export const metadata = { title: "Admin" };
export const dynamic = "force-dynamic";

/** Private owner dashboard. Only profiles with is_admin = true can see it; everyone else gets a 404. */
export default async function AdminPage() {
  const { user } = await requireUser();
  if (!user) notFound();
  const me = await getProfile(user.id, user.email);
  if (!me.is_admin) notFound();

  const db = createAdminClient();
  const period = currentPeriod();
  const [profiles, projectCount, chapters, usage] = await Promise.all([
    db.from("profiles").select("id, email, plan, is_admin, subscription_status, created_at").order("created_at", { ascending: false }),
    db.from("projects").select("id", { count: "exact", head: true }),
    db.from("chapters").select("word_count"),
    db.from("ai_usage").select("tokens, requests").eq("period", period),
  ]);

  const people = profiles.data ?? [];
  const byPlan = { free: 0, pro: 0, studio: 0 } as Record<string, number>;
  for (const p of people) if (!p.is_admin) byPlan[p.plan] = (byPlan[p.plan] ?? 0) + 1;
  const words = (chapters.data ?? []).reduce((a, c) => a + (c.word_count || 0), 0);
  const tokens = (usage.data ?? []).reduce((a, u) => a + (u.tokens || 0), 0);
  const requests = (usage.data ?? []).reduce((a, u) => a + (u.requests || 0), 0);
  // Display prices are monthly list prices; yearly subscribers make this an estimate.
  const mrr = byPlan.pro * 9 + byPlan.studio * 19;

  const stats = [
    { icon: Users, label: "Users", value: compact(people.length), sub: `${byPlan.free} free · ${byPlan.pro} pro · ${byPlan.studio} studio` },
    { icon: Sparkles, label: "Est. monthly revenue", value: `$${mrr}`, sub: "at monthly list prices" },
    { icon: BookOpen, label: "Projects", value: compact(projectCount.count ?? 0), sub: `${compact(words)} words written` },
    { icon: Feather, label: "AI this month", value: compact(tokens), sub: `${compact(requests)} requests (included AI)` },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-muted">Owner dashboard</p>
          <h1 className="mt-1 font-serif text-3xl font-semibold sm:text-4xl">Admin</h1>
        </div>
        <Badge tone="accent">Only visible to admins</Badge>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="card p-5">
            <div className="flex items-center gap-2 text-xs text-muted">
              <s.icon size={14} className="text-accent" /> {s.label}
            </div>
            <p className="mt-2 text-2xl font-semibold">{s.value}</p>
            <p className="mt-1 text-xs text-muted">{s.sub}</p>
          </div>
        ))}
      </div>

      <section className="card mt-8 overflow-hidden">
        <div className="border-b border-line px-5 py-4">
          <h2 className="font-semibold">Users</h2>
          <p className="text-xs text-muted">Newest first</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs text-muted">
                <th className="px-5 py-2 font-medium">Email</th>
                <th className="px-5 py-2 font-medium">Plan</th>
                <th className="px-5 py-2 font-medium">Billing</th>
                <th className="px-5 py-2 font-medium">Joined</th>
              </tr>
            </thead>
            <tbody>
              {people.slice(0, 100).map((p) => (
                <tr key={p.id} className="border-b border-line last:border-0">
                  <td className="px-5 py-2.5">{p.email}</td>
                  <td className="px-5 py-2.5">
                    {p.is_admin ? <Badge tone="accent">Admin</Badge> : <Badge>{p.plan}</Badge>}
                  </td>
                  <td className="px-5 py-2.5 text-muted">{p.subscription_status ?? "—"}</td>
                  <td className="px-5 py-2.5 text-muted">{timeAgo(p.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
