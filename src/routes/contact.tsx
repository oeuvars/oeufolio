import { createFileRoute } from '@tanstack/react-router'

import { pages } from '../content'
import { seo } from '../lib/seo'

export const Route = createFileRoute('/contact')({ head: () => seo(pages.contact), component: Contact })

/** The page is the ticket, which lies in its strip whether the page is open or not (SiteShell, ticket/Ticket.tsx). */
function Contact() {
  return <h1 className="sr-only">Contact</h1>
}
