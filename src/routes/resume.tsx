import { createFileRoute } from '@tanstack/react-router'

import { ResumePage } from '../components/ResumePage'
import { pages } from '../content'
import { seo } from '../lib/seo'

/** The résumé as a page of text, outside the stack of folders. The badge opens it. */
export const Route = createFileRoute('/resume')({
  staticData: { bare: true },
  head: () => seo(pages.resume),
  component: ResumePage,
})
