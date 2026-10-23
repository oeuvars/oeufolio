import { createFileRoute } from '@tanstack/react-router'

import { Letter } from '../components/letter'
import { pages, profile } from '../content'
import { seo } from '../lib/seo'

/** The things I like, as a letter about them to a younger me. */
const LetterPage = () => {
  return (
    // The letter has already grown out of its folded strip's picture by the time its page shows (Fold).
    <>
      <h1 className="sr-only">Things I like</h1>
      <Letter letter={profile.letter} />
    </>
  )
}

export const Route = createFileRoute('/letter')({ head: () => seo(pages.letter), component: LetterPage })
