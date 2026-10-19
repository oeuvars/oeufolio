import { createFileRoute } from '@tanstack/react-router'

import { Waybill } from '../components/Waybill'
import { pages } from '../content'
import { seo } from '../lib/seo'

/** The résumé as a shipping label and its packing slip, outside the stack of folders. The badge opens it. */
export const Route = createFileRoute('/resume')({
  staticData: { bare: true },
  head: () => seo(pages.resume),
  component: Waybill,
})
