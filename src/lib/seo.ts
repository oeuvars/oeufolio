import { profile, site } from '../content'
import type { PageMeta } from '../types'

/**
 * The head of a page: its title and summary for search engines, the Open Graph and X card tags a link to it
 * unfurls from, and its canonical address, which drops any query (the work page's building at /work?v=1 is
 * still /work).
 */
export function seo({ path, title, description, preview }: PageMeta) {
  const url = new URL(path, site.url).href
  const image = new URL(preview.src, site.url).href

  return {
    meta: [
      { title },
      { name: 'description', content: description },
      { property: 'og:type', content: 'website' },
      { property: 'og:url', content: url },
      { property: 'og:title', content: title },
      { property: 'og:description', content: description },
      { property: 'og:image', content: image },
      { property: 'og:image:type', content: 'image/jpeg' },
      { property: 'og:image:width', content: '1200' },
      { property: 'og:image:height', content: '630' },
      { property: 'og:image:alt', content: preview.alt },
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: title },
      { name: 'twitter:description', content: description },
      { name: 'twitter:image', content: image },
      { name: 'twitter:image:alt', content: preview.alt },
    ],
    links: [{ rel: 'canonical', href: url }],
  }
}

/** Who the site is about, as schema.org data a search engine can read: the home page's head carries it. */
export function person() {
  return {
    type: 'application/ld+json',
    children: JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'Person',
      name: site.name,
      alternateName: profile.handle,
      url: new URL('/', site.url).href,
      jobTitle: 'Product engineer',
      worksFor: { '@type': 'Organization', name: profile.extras.company.label, url: profile.extras.company.href },
      address: { '@type': 'PostalAddress', addressLocality: 'Kolkata', addressCountry: 'IN' },
      sameAs: profile.socials.map((social) => social.href),
    }),
  }
}
