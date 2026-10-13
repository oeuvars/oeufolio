import { createFileRoute } from '@tanstack/react-router'

import { Badge } from '../components/Badge'
import { profile } from '../content'

export const Route = createFileRoute('/')({ component: Basics })

function Basics() {
  return <Badge badge={profile.badge} />
}
