import TrashView, { type TrashedBook } from "@/components/app/TrashView";
import { requireUser } from "@/lib/supabase/server";

export const metadata = { title: "Trash" };

export default async function TrashPage() {
  const { supabase } = await requireUser();
  const { data } = await supabase
    .from("projects")
    .select("id, title, deleted_at, chapters(word_count)")
    .not("deleted_at", "is", null)
    .order("deleted_at", { ascending: false });

  const books: TrashedBook[] = (data ?? []).map((p) => ({
    id: p.id,
    title: p.title,
    deleted_at: p.deleted_at as string,
    words: ((p.chapters as { word_count: number }[]) ?? []).reduce((a, c) => a + (c.word_count || 0), 0),
    chapters: ((p.chapters as unknown[]) ?? []).length,
  }));
  return <TrashView books={books} />;
}
