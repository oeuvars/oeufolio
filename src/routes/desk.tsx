import { createFileRoute } from '@tanstack/react-router'

import { pages } from '../content'
import { seo } from '../lib/seo'

export const Route = createFileRoute('/desk')({ head: () => seo(pages.desk), component: Extras })

/** The page is the desk, which lies in its strip whether the page is open or not (SiteShell, mat/Desk.tsx). */
function Extras() {
  return <h1 className="sr-only">Extras</h1>
}
