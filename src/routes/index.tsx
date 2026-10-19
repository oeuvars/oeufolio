import { createFileRoute } from '@tanstack/react-router'

import { pages } from '../content'
import { person, seo } from '../lib/seo'

/** The first page is the badge, and SiteShell hangs that in the strip itself, folded or not. */
const Basics = () => {
  return null
}

export const Route = createFileRoute('/')({
  head: () => ({ ...seo(pages.basics), scripts: [person()] }),
  component: Basics,
})
