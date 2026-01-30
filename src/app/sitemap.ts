import { MetadataRoute } from 'next'

const sitemap = (): MetadataRoute.Sitemap => {
  const baseUrl = 'https://anurag.gg'

  return [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 1,
    },
  ]
}

export default sitemap
