import { notFound, redirect } from "next/navigation";
import Workspace from "@/components/workspace/Workspace";
import { planFor } from "@/lib/plans";
import { getProfile, requireUser } from "@/lib/supabase/server";
import type { Chapter, Entity, EntityLink, Project } from "@/lib/types";

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase, user } = await requireUser();
  const [{ data: project }, { data: chapters }, { data: entities }, { data: links }, profile] = await Promise.all([
    supabase.from("projects").select("*").eq("id", id).maybeSingle(),
    supabase.from("chapters").select("*").eq("project_id", id).order("position"),
    supabase.from("entities").select("*").eq("project_id", id).order("name"),
    supabase.from("entity_links").select("id, project_id, source_id, target_id, kind, note").eq("project_id", id),
    getProfile(user!.id, user!.email),
  ]);
  if (!project) notFound();
  if (project.deleted_at) redirect("/app/trash");
  return (
    <Workspace
      initialProject={project as Project}
      initialChapters={(chapters ?? []) as Chapter[]}
      initialEntities={(entities ?? []) as Entity[]}
      initialLinks={(links ?? []) as EntityLink[]}
      docxExport={planFor(profile).docxExport}
    />
  );
}
