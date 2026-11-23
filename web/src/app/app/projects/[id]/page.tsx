import { notFound } from "next/navigation";
import Workspace from "@/components/workspace/Workspace";
import { planFor } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";
import type { Chapter, Entity, Project } from "@/lib/types";

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase, user } = await requireUser();
  const [{ data: project }, { data: chapters }, { data: entities }, profile] = await Promise.all([
    supabase.from("projects").select("*").eq("id", id).maybeSingle(),
    supabase.from("chapters").select("*").eq("project_id", id).order("position"),
    supabase.from("entities").select("*").eq("project_id", id).order("name"),
    getProfile(user!.id, user!.email),
  ]);
  if (!project) notFound();
  return (
    <Workspace
      initialProject={project as Project}
      initialChapters={(chapters ?? []) as Chapter[]}
      initialEntities={(entities ?? []) as Entity[]}
      docxExport={planFor(profile).docxExport}
    />
  );
}
