import "server-only";

/**
 * Book art (covers, illustrations), clean and unwatermarked.
 *
 * Providers, in order:
 *  1. Cloudflare Workers AI, FLUX.2 [klein] 4B: free daily allowance, no card, no watermark.
 *     Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_AI_TOKEN (a token with "Workers AI" permission).
 *  2. Pollinations with POLLINATIONS_TOKEN (its anonymous tier adds a logo and is throttled, so it's never used without a key).
 * With neither configured, art is switched off rather than served watermarked or low resolution.
 *
 * The same prompt + seed + size gives the same picture, so only those settings are stored.
 */

export interface ImageSpec {
  prompt: string;
  seed: number;
  width: number;
  height: number;
}

export { ART_STYLES, fullPrompt } from "./art-styles";

export class ImageError extends Error {
  constructor(
    message: string,
    public status = 502,
  ) {
    super(message);
  }
}

export function imagesConfigured(): boolean {
  return !!((process.env.CLOUDFLARE_ACCOUNT_ID && process.env.CLOUDFLARE_AI_TOKEN) || process.env.POLLINATIONS_TOKEN);
}

export function clampSpec(spec: Partial<ImageSpec>): ImageSpec {
  const n = (v: unknown, lo: number, hi: number, d: number) => {
    const x = Math.round(Number(v));
    return Number.isFinite(x) ? Math.min(hi, Math.max(lo, x)) : d;
  };
  return {
    prompt: String(spec.prompt ?? "").slice(0, 1600),
    seed: n(spec.seed, 0, 2_000_000_000, 1),
    // Workers AI FLUX.2 accepts 256-1920 on each side; keep multiples of 16.
    width: Math.round(n(spec.width, 256, 1920, 1024) / 16) * 16,
    height: Math.round(n(spec.height, 256, 1920, 1024) / 16) * 16,
  };
}

async function cloudflare(spec: ImageSpec): Promise<{ bytes: ArrayBuffer; type: string }> {
  const form = new FormData();
  form.set("prompt", spec.prompt);
  form.set("width", String(spec.width));
  form.set("height", String(spec.height));
  form.set("seed", String(spec.seed));
  const url = `https://api.cloudflare.com/client/v4/accounts/${process.env.CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-2-klein-4b`;
  for (let attempt = 0; attempt < 2; attempt++) {
    const res = await fetch(url, {
      method: "POST",
      headers: { Authorization: `Bearer ${process.env.CLOUDFLARE_AI_TOKEN}` },
      body: form,
      signal: AbortSignal.timeout(55_000),
    });
    if (res.ok) {
      const data = (await res.json()) as { result?: { image?: string }; image?: string };
      const b64 = data.result?.image ?? data.image;
      if (!b64) throw new ImageError("The image service returned no picture. Please try again.");
      const bytes = Buffer.from(b64, "base64");
      const type = bytes[0] === 0x89 ? "image/png" : bytes[0] === 0x52 ? "image/webp" : "image/jpeg";
      return { bytes: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer, type };
    }
    const body = await res.text().catch(() => "");
    console.error(`Cloudflare image ${res.status}: ${body.slice(0, 300)}`);
    if (res.status === 429 && attempt === 0) {
      await new Promise((r) => setTimeout(r, 3000));
      continue;
    }
    if (res.status === 429 || /daily|neurons|limit/i.test(body)) {
      throw new ImageError("Today's free picture allowance is used up. It resets at midnight UTC.", 429);
    }
    throw new ImageError("The image couldn't be created just now. Please try again.");
  }
  throw new ImageError("The image service is busy. Please try again in a minute.", 429);
}

async function pollinations(spec: ImageSpec): Promise<{ bytes: ArrayBuffer; type: string }> {
  const params = new URLSearchParams({ width: String(spec.width), height: String(spec.height), seed: String(spec.seed), model: "flux", nologo: "true", enhance: "false" });
  const res = await fetch(`https://image.pollinations.ai/prompt/${encodeURIComponent(spec.prompt)}?${params}`, {
    headers: { Authorization: `Bearer ${process.env.POLLINATIONS_TOKEN}` },
    signal: AbortSignal.timeout(55_000),
  });
  if (res.ok && (res.headers.get("content-type") ?? "").startsWith("image/")) {
    return { bytes: await res.arrayBuffer(), type: res.headers.get("content-type") ?? "image/jpeg" };
  }
  console.error(`Pollinations ${res.status}: ${(await res.text().catch(() => "")).slice(0, 300)}`);
  throw new ImageError("The image couldn't be created just now. Please try again.");
}

/** Fetch the image bytes from the configured provider. */
export async function renderImage(spec: ImageSpec): Promise<{ bytes: ArrayBuffer; type: string }> {
  if (process.env.CLOUDFLARE_ACCOUNT_ID && process.env.CLOUDFLARE_AI_TOKEN) return cloudflare(spec);
  if (process.env.POLLINATIONS_TOKEN) return pollinations(spec);
  throw new ImageError("Book art isn't switched on yet.", 503);
}
