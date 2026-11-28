import "server-only";
import { clampSpec, renderImage } from "./images";
import { createAdminClient } from "./supabase/server";

const BUCKET = "book-art";

/**
 * A saved cover or illustration's bytes. Painted once, then kept in Supabase Storage so page views
 * and exports don't spend the image provider's daily allowance again. The caller must already have
 * checked the writer owns the image (RLS select).
 */
export async function savedImage(img: { id: string; user_id: string; prompt: string; seed: number; width: number; height: number }) {
  const admin = createAdminClient();
  const path = `${img.user_id}/${img.id}-${img.seed}`;
  const { data } = await admin.storage.from(BUCKET).download(path);
  if (data) return { bytes: await data.arrayBuffer(), type: data.type || "image/jpeg" };
  const rendered = await renderImage(clampSpec(img));
  await admin.storage.from(BUCKET).upload(path, rendered.bytes, { contentType: rendered.type, upsert: true }).catch(() => {});
  return rendered;
}

/** Remove stored copies of an image (all seeds). */
export async function forgetImage(userId: string, id: string) {
  const admin = createAdminClient();
  const { data } = await admin.storage.from(BUCKET).list(userId, { search: id });
  const paths = (data ?? []).map((f) => `${userId}/${f.name}`);
  if (paths.length) await admin.storage.from(BUCKET).remove(paths);
}
