import { createFileRoute } from '@tanstack/react-router'

import { Ticket } from '../components/ticket/Ticket'

export const Route = createFileRoute('/contact')({ component: Contact })

/** How to reach me, printed on a cinema ticket. */
function Contact() {
  return <Ticket />
}
