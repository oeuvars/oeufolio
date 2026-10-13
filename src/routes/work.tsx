import { createFileRoute } from '@tanstack/react-router'

import { Dollhouse } from '../components/Dollhouse'
import { Masthead } from '../components/Masthead'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/work')({ component: Work })

/** A red sawtooth on marigold, as a tile: the border printed down the poster's left edge. */
const sawtooth =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 20' preserveAspectRatio='none'%3E%3Crect width='10' height='20' fill='%23f2b632'/%3E%3Cpath d='M0 0 10 10 0 20Z' fill='%23b3291b'/%3E%3C/svg%3E\")"

/**
 * Where I've worked, as the poster for a film about it: a masthead, and under it a still of a building cut
 * open from the roof to the street, with a floor for each job. Everything on the sheet is sized off the
 * sheet's width, so it scales as a print would, and the sheet is no wider than lets the whole of it show at
 * once: the page's own margins above and below are given over to it.
 */
function Work() {
  const { experience, handle, nav } = profile
  const issue = nav.findIndex((item) => item.to === '/work') + 1

  return (
    <div className="@container/box w-full font-futura">
      <div className="@container mx-auto @md/box:-my-[4vh] @md/box:max-w-[74vh]">
        <div className="relative pl-[4.6cqw] text-[12px] leading-[1.4] @md/box:text-[2cqw]">
          <div
            aria-hidden
            className="absolute inset-y-0 left-0 w-[2.4cqw] bg-size-[100%_4.8cqw]"
            style={{ backgroundImage: sawtooth }}
          />

          <Reveal delay={0.1}>
            <Masthead presenter={handle} issue={issue} />
          </Reveal>

          <Reveal delay={0.3} className="mt-[1cqw]">
            <h2 className="sr-only">Experience</h2>
            <Dollhouse roles={experience} />
          </Reveal>
        </div>
      </div>
    </div>
  )
}
