import Link from "next/link";
import NewProjectForm from "@/components/NewProjectForm";
import { getPlan } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";

export default async function ProjectsPage() {
  const { supabase, user } = await requireUser();
  const profile = await getProfile(user!.id, user!.email);
  const plan = getPlan(profile.plan);

  const { data: projects } = await supabase
    .from("projects")
    .select("id, title, genre, premise, target_words, updated_at, chapters(word_count)")
    .order("updated_at", { ascending: false });

  const list = (projects ?? []).map((p) => ({
    ...p,
    words: ((p.chapters as { word_count: number }[]) ?? []).reduce((a, c) => a + (c.word_count || 0), 0),
    chapterCount: ((p.chapters as unknown[]) ?? []).length,
  }));
  const atLimit = list.length >= plan.maxProjects;

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Projects</h1>
          <p className="mt-1 text-sm text-muted">
            {plan.maxProjects === Infinity
              ? `${list.length} project${list.length === 1 ? "" : "s"}`
              : `${list.length} of ${plan.maxProjects} projects on the ${plan.name} plan`}
          </p>
        </div>
      </div>

      <div className="mt-8">
        <NewProjectForm atLimit={atLimit} planName={plan.name} />
      </div>

      {list.length === 0 ? (
        <div className="card mt-8 p-10 text-center">
          <p className="text-lg font-medium">No projects yet</p>
          <p className="mt-1 text-sm text-muted">Create your first project above to start planning your book.</p>
        </div>
      ) : (
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {list.map((p) => {
            const pct = Math.min(100, Math.round((p.words / (p.target_words || 80000)) * 100));
            return (
              <Link key={p.id} href={`/app/projects/${p.id}`} className="card block p-5 transition hover:border-accent/50">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="font-serif text-lg font-semibold">{p.title}</h2>
                  {p.genre && <span className="shrink-0 rounded-full bg-panel-2 px-2 py-0.5 text-xs text-muted">{p.genre}</span>}
                </div>
                {p.premise && <p className="mt-2 line-clamp-2 text-sm text-muted">{p.premise}</p>}
                <div className="mt-4 h-1.5 rounded-full bg-panel-2">
                  <div className="h-1.5 rounded-full bg-accent" style={{ width: `${pct}%` }} />
                </div>
                <p className="mt-2 text-xs text-muted">
                  {p.words.toLocaleString()} / {(p.target_words || 80000).toLocaleString()} words · {p.chapterCount} chapter
                  {p.chapterCount === 1 ? "" : "s"} · updated {new Date(p.updated_at).toLocaleDateString()}
                </p>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
