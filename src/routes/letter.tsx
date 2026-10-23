import { createFileRoute } from '@tanstack/react-router'

import { Letter } from '../components/letter'
import { Reveal } from '../components/reveal'
import { pages, profile } from '../content'
import { seo } from '../lib/seo'

/** The things I like, as a letter about them to a younger me. */
const LetterPage = () => {
  return (
    // On a phone the letter has already grown out of its folded strip's band by the time its page shows (Fold).
    <Reveal delay={0.1} className="max-md:transform-none! max-md:opacity-100!">
      <h1 className="sr-only">Things I like</h1>
      <Letter letter={profile.letter} />
    </Reveal>
  )
}

export const Route = createFileRoute('/letter')({ head: () => seo(pages.letter), component: LetterPage })
