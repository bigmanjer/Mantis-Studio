import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/env";

const site = siteUrl();

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/app", "/api", "/auth"] }],
    sitemap: `${site}/sitemap.xml`,
  };
}
