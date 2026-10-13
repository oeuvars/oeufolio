import { createFileRoute } from '@tanstack/react-router'

import { Dollhouse } from '../components/Dollhouse'
import { Masthead } from '../components/Masthead'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/work')({ component: Work })

/**
 * Where I've worked, as the poster for a film about it: a masthead, and coming up behind it a picture of a
 * building cut open from the roof to the street, with a floor for each job. The sheet is no wider than
 * lets the whole of it show at once: the page's own margins above and below are given over to it. The
 * title is sized off the sheet, and the picture runs past it on either side, as far as the page has room.
 */
function Work() {
  const { experience, handle } = profile

  return (
    <div className="@container/box w-full font-futura">
      <div className="@md/box:-my-[4vh]">
        <div className="@container relative z-10 mx-auto text-[12px] leading-[1.4] @md/box:max-w-[73vh] @md/box:text-[2cqw]">
          <Reveal delay={0.1}>
            <Masthead presenter={handle} />
          </Reveal>
        </div>

        <Reveal delay={0.3}>
          <h2 className="sr-only">Experience</h2>
          <Dollhouse roles={experience} />
        </Reveal>
      </div>
    </div>
  )
}
