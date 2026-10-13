import { createFileRoute } from '@tanstack/react-router'

import { Letter } from '../components/Letter'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/likes')({ component: Likes })

/** The things I like, as a letter about them to a younger me. */
function Likes() {
  return (
    <Reveal delay={0.1}>
      <h1 className="sr-only">Things I like</h1>
      <Letter letter={profile.letter} />
    </Reveal>
  )
}
