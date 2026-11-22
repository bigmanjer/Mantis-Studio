import ProjectsView, { type ProjectSummary } from "@/components/app/ProjectsView";
import { getPlan } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";

export const metadata = { title: "Projects" };

export default async function ProjectsPage() {
  const { supabase, user } = await requireUser();
  const profile = await getProfile(user!.id, user!.email);
  const plan = getPlan(profile.plan);

  const { data } = await supabase
    .from("projects")
    .select("id, title, genre, premise, target_words, updated_at, chapters(word_count)")
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

  return <ProjectsView projects={projects} planName={plan.name} maxProjects={plan.maxProjects} email={user!.email ?? ""} />;
}
