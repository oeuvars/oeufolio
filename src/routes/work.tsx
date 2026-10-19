import { createFileRoute } from '@tanstack/react-router'

import { Dollhouse } from '../components/dollhouse'
import { Masthead } from '../components/masthead'
import { Poster } from '../components/poster'
import { Reveal } from '../components/reveal'
import { pages, profile } from '../content'
import { seo } from '../lib/seo'
import type { VersionSearch } from '../types'

/** Two versions of the page: the poster (the default), and the building it replaced at /work?v=1. */
export const Route = createFileRoute('/work')({
  validateSearch: (search: Record<string, unknown>): VersionSearch => (Number(search.v) === 1 ? { v: 1 } : {}),
  head: () => seo(pages.work),
  component: Work,
})

function Work() {
  const { v } = Route.useSearch()

  return v === 1 ? <Building /> : <Poster />
}

/**
 * Where I've worked, as the poster for a film about it: a title, and coming up behind it a picture of a
 * building cut open from the roof to the street, with a floor for each job. The picture stands on the foot
 * of the page and runs off both its sides, darkening a little as it goes. The page's own margins are given
 * over to it: the ones undone here are SiteShell's padding round a page. The title
 * is sized off a sheet no wider than lets the whole building show at once.
 */
function Building() {
  const { experience } = profile

  return (
    <div className="@container/box flex flex-col justify-end font-futura [mask-image:linear-gradient(to_right,transparent,#000_6.5%,#000_93.5%,transparent)] md:-my-[6.4vh] md:-mr-[clamp(1rem,2.6vw,3rem)] md:-ml-[4.1rem] md:min-h-[99.8vh]">
      <div className="@container relative z-10 mx-auto w-full text-[12px] leading-[1.4] md:max-w-[80vh] md:text-[2cqw]">
        <Reveal delay={0.45}>
          <Masthead />
        </Reveal>
      </div>

      <h2 className="sr-only">Experience</h2>
      <Dollhouse roles={experience} />
    </div>
  )
}
