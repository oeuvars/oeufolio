import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/contact')({ component: Contact })

/** The page is the ticket, which lies in its strip whether the page is open or not (SiteShell, ticket/Ticket.tsx). */
function Contact() {
  return <h1 className="sr-only">Contact</h1>
}
