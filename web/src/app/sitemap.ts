import type { MetadataRoute } from "next";

const site = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/pricing", "/signup", "/legal/terms", "/legal/privacy"].map((path) => ({
    url: `${site}${path}`,
    changeFrequency: path === "" || path === "/pricing" ? "weekly" : "yearly",
    priority: path === "" ? 1 : 0.6,
  }));
}
