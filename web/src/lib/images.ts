import "server-only";

/**
 * Book art (covers, illustrations). Uses Pollinations (free, no card). Set POLLINATIONS_TOKEN
 * (free account at auth.pollinations.ai) to remove the provider's logo and get priority.
 * Images are deterministic for the same prompt, seed and size, so only those settings are stored.
 */

export interface ImageSpec {
  prompt: string;
  seed: number;
  width: number;
  height: number;
}

export { ART_STYLES, fullPrompt } from "./art-styles";

export function clampSpec(spec: Partial<ImageSpec>): ImageSpec {
  const n = (v: unknown, lo: number, hi: number, d: number) => {
    const x = Math.round(Number(v));
    return Number.isFinite(x) ? Math.min(hi, Math.max(lo, x)) : d;
  };
  return {
    prompt: String(spec.prompt ?? "").slice(0, 1600),
    seed: n(spec.seed, 0, 2_000_000_000, 1),
    width: n(spec.width, 256, 1600, 1024),
    height: n(spec.height, 256, 2048, 1024),
  };
}

/** Fetch the image bytes. Throws a writer-friendly Error when the service fails. */
export async function renderImage(spec: ImageSpec): Promise<{ bytes: ArrayBuffer; type: string }> {
  const token = process.env.POLLINATIONS_TOKEN;
  const params = new URLSearchParams({
    width: String(spec.width),
    height: String(spec.height),
    seed: String(spec.seed),
    model: "flux",
    nologo: "true",
    enhance: "false",
    referrer: "mantis-studio",
  });
  const url = `https://image.pollinations.ai/prompt/${encodeURIComponent(spec.prompt)}?${params}`;
  let last = 0;
  for (let attempt = 0; attempt < 2; attempt++) {
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: AbortSignal.timeout(55_000),
    });
    last = res.status;
    if (res.ok && (res.headers.get("content-type") ?? "").startsWith("image/")) {
      return { bytes: await res.arrayBuffer(), type: res.headers.get("content-type") ?? "image/jpeg" };
    }
    await res.body?.cancel().catch(() => {});
    if (res.status !== 429 && res.status < 500) break;
    await new Promise((r) => setTimeout(r, 3000));
  }
  console.error(`Image service returned ${last}`);
  throw new Error(last === 429 ? "The image service is busy. Please try again in a minute." : "The image couldn't be created just now. Please try again.");
}
