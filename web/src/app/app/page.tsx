import Link from "next/link";
import ProjectsView, {
  type ProjectSummary,
} from "@/components/app/ProjectsView";
import { planFor } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";

export const metadata = { title: "Projects" };

export default async function ProjectsPage({
  searchParams,
}: {
  searchParams: Promise<{ trashed?: string }>;
}) {
  const { supabase, user } = await requireUser();
  const profile = await getProfile(user!.id, user!.email);
  const plan = planFor(profile);

  // Books in the Trash for more than 30 days are deleted for good.
  await supabase
    .from("projects")
    .delete()
    .lt("deleted_at", new Date(Date.now() - 30 * 86_400_000).toISOString());

  const { data } = await supabase
    .from("projects")
    .select(
      "id, title, genre, premise, target_words, updated_at, chapters(word_count)",
    )
    .is("deleted_at", null)
    .order("updated_at", { ascending: false });

  const projects: ProjectSummary[] = (data ?? []).map((p) => {
    const chapters = (p.chapters as { word_count: number }[]) ?? [];
    return {
      id: p.id,
      title: p.title,
      genre: p.genre,
      premise: p.premise,
      target_words: p.target_words,
      updated_at: p.updated_at,
      words: chapters.reduce((a, c) => a + (c.word_count || 0), 0),
      chapterCount: chapters.length,
    };
  });

  const since = new Date(Date.now() - 62 * 86_400_000)
    .toISOString()
    .slice(0, 10);
  const [{ data: days }, { count: entityCount }, { data: usage }] =
    await Promise.all([
      supabase.from("writing_days").select("day, words").gte("day", since),
      supabase.from("entities").select("id", { count: "exact", head: true }),
      supabase.from("ai_usage").select("requests"),
    ]);
  const totalWords = projects.reduce((a, p) => a + p.words, 0);

  const { trashed } = await searchParams;
  return (
    <>
      {trashed === "1" && (
        <div className="mx-auto max-w-6xl px-4 pt-6 sm:px-8" role="status">
          <p className="rounded-lg border border-line bg-panel px-4 py-2.5 text-sm text-muted">
            Moved to the Trash. You can restore it for 30 days.{" "}
            <Link
              href="/app/trash"
              className="font-medium text-accent hover:underline"
            >
              Open Trash
            </Link>
          </p>
        </div>
      )}
      <ProjectsView
        projects={projects}
        planName={plan.name}
        maxProjects={plan.maxProjects}
        email={user!.email ?? ""}
        writing={{
          days: (days ?? []) as { day: string; words: number }[],
          goal: (profile as { daily_goal?: number }).daily_goal ?? 500,
        }}
        onboarding={{
          hasProject: projects.length > 0,
          wrote100: totalWords >= 100,
          usedAi: (usage ?? []).some((u) => (u.requests ?? 0) > 0),
          hasWorldEntry: (entityCount ?? 0) > 0,
          atLimit: projects.length >= plan.maxProjects,
        }}
      />
    </>
  );
}
