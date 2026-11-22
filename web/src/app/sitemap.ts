import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/env";

const site = siteUrl();

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/pricing", "/signup", "/legal/terms", "/legal/privacy"].map((path) => ({
    url: `${site}${path}`,
    changeFrequency: path === "" || path === "/pricing" ? "weekly" : "yearly",
    priority: path === "" ? 1 : 0.6,
  }));
}
