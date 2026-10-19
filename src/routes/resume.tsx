import { createFileRoute } from '@tanstack/react-router'

import { Vitrine } from '../components/vitrine'
import { pages } from '../content'
import { seo } from '../lib/seo'

/** The résumé behind glass, outside the stack of folders. The badge opens it. */
export const Route = createFileRoute('/resume')({
  staticData: { bare: true },
  head: () => seo(pages.resume),
  component: Vitrine,
})
