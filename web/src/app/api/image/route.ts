import { NextResponse } from "next/server";
import { clampSpec, renderImage } from "@/lib/images";
import { requireUser } from "@/lib/supabase/server";

export const maxDuration = 60;

/**
 * Book art for signed-in writers.
 *   ?id=<book_images id>                    a saved cover or illustration (owner only, via RLS)
 *   ?prompt=…&seed=…&width=…&height=…       a preview that isn't saved yet
 * Same settings always give the same picture, so responses are cached by the browser.
 */
export async function GET(req: Request) {
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "Please log in." }, { status: 401 });
  const q = new URL(req.url).searchParams;

  let spec;
  const id = q.get("id");
  if (id) {
    const { data } = await supabase.from("book_images").select("prompt, seed, width, height").eq("id", id).maybeSingle();
    if (!data) return NextResponse.json({ error: "Not found" }, { status: 404 });
    spec = clampSpec(data);
  } else {
    spec = clampSpec({ prompt: q.get("prompt") ?? "", seed: Number(q.get("seed")), width: Number(q.get("width")), height: Number(q.get("height")) });
    if (!spec.prompt.trim()) return NextResponse.json({ error: "Missing prompt" }, { status: 400 });
  }

  try {
    const { bytes, type } = await renderImage(spec);
    return new NextResponse(bytes, {
      headers: { "Content-Type": type, "Cache-Control": "private, max-age=31536000, immutable" },
    });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : "Image failed." }, { status: 502 });
  }
}
