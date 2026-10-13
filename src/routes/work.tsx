import { createFileRoute } from '@tanstack/react-router'

import { Dollhouse } from '../components/Dollhouse'
import { Masthead } from '../components/Masthead'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/work')({ component: Work })

/**
 * Where I've worked, as the poster for a film about it: a masthead, and coming up behind it a picture of a
 * building cut open from the roof to the street, with a floor for each job. Everything on the sheet is
 * sized off the sheet's width, so it scales as a print would, and the sheet is no wider than lets the whole
 * of it show at once: the page's own margins above and below are given over to it.
 */
function Work() {
  const { experience, handle } = profile

  return (
    <div className="@container/box w-full font-futura">
      <div className="@container mx-auto @md/box:-my-[4vh] @md/box:max-w-[70vh]">
        <div className="text-[12px] leading-[1.4] @md/box:text-[2cqw]">
          <Reveal delay={0.1} className="relative z-10">
            <Masthead presenter={handle} />
          </Reveal>

          <Reveal delay={0.3}>
            <h2 className="sr-only">Experience</h2>
            <Dollhouse roles={experience} />
          </Reveal>
        </div>
      </div>
    </div>
  )
}
