import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/extras')({ component: Extras })

/** The page is the desk, which lies in its strip whether the page is open or not (SiteShell, mat/Desk.tsx). */
function Extras() {
  return <h1 className="sr-only">Extras</h1>
}
