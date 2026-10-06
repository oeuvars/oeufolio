import type { MetadataRoute } from "next"
import { SITE_URL } from "@/lib/site"
import { getExhibitions, getGalleries } from "@/lib/data"

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date()

  return [
    {
      url: `${SITE_URL}/`,
      lastModified,
      changeFrequency: "monthly",
      priority: 1,
    },
    ...(getExhibitions().length > 0
      ? [{
          url: `${SITE_URL}/exhibitions`,
          lastModified,
          changeFrequency: "monthly" as const,
          priority: 0.8,
        }]
      : []),
    ...getGalleries().map((g) => ({
      url: `${SITE_URL}/galleries/${g.id}`,
      lastModified,
      changeFrequency: "monthly" as const,
      priority: 0.9,
    })),
  ]
}
