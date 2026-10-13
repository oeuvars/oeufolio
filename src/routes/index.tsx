import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({ component: Basics })

/** The first page is the badge, and SiteShell hangs that in the strip itself, folded or not. */
function Basics() {
  return null
}
