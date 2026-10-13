import { createFileRoute } from '@tanstack/react-router'

import { Floor } from '../components/Floor'
import { Masthead } from '../components/Masthead'
import { Reveal } from '../components/Reveal'
import { Shop } from '../components/Shop'
import { Roof } from '../components/scenes/Roof'
import { profile } from '../content'

export const Route = createFileRoute('/work')({ component: Work })

/** A red sawtooth on marigold, as a tile: the border printed down the poster's left edge. */
const sawtooth =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 20' preserveAspectRatio='none'%3E%3Crect width='10' height='20' fill='%23f2b632'/%3E%3Cpath d='M0 0 10 10 0 20Z' fill='%23b3291b'/%3E%3C/svg%3E\")"

/**
 * Where I've worked, as the poster for a film about it. Under the masthead is a building cut open from the
 * roof to the street: a floor for each job, the newest at the top, and the projects as the shops at the
 * bottom. Everything on the sheet is sized off the sheet's width, so it scales as a print would.
 */
function Work() {
  const { experience, works, handle, nav } = profile
  const issue = nav.findIndex((item) => item.to === '/work') + 1

  return (
    <div className="@container w-full font-futura">
      <div className="relative pl-[4.6cqw] text-[clamp(12px,2.5cqw,17px)] leading-[1.4]">
        <div
          aria-hidden
          className="absolute inset-y-0 left-0 w-[2.4cqw] bg-size-[100%_4.8cqw]"
          style={{ backgroundImage: sawtooth }}
        />

        <Reveal delay={0.1}>
          <Masthead presenter={handle} issue={issue} parts={experience.length} works={works.length} />
        </Reveal>

        <Reveal delay={0.3} className="mt-[3cqw] px-[2.5cqw]">
          <section>
            <h2 className="sr-only">Experience</h2>
            <div className="-mx-[2.5cqw]">
              <Roof sign="Experience" />
            </div>
            <ol className="flex flex-col gap-[1.3cqw] border-t-[1cqw] border-cream bg-mendl p-[1.3cqw] pb-0">
              {experience.map((role, i) => (
                <li key={`${role.org}-${role.period}`}>
                  <Floor role={role} part={experience.length - i} index={i} />
                </li>
              ))}
            </ol>
          </section>

          <section className="bg-mendl px-[1.3cqw] pt-[1.3cqw]">
            <h2 className="flex items-center justify-center gap-[1em] border-y-[0.5cqw] border-cream bg-cocoa py-[0.55em] text-[0.74em] font-bold tracking-[0.36em] text-cream uppercase">
              <span aria-hidden>★</span>
              Selected works
              <span aria-hidden>★</span>
            </h2>
            <ul className="grid grid-cols-1 gap-[1.3cqw] pt-[1.3cqw] @md:grid-cols-3">
              {works.map((work, i) => (
                <li key={work.title}>
                  <Shop work={work} index={i} />
                </li>
              ))}
            </ul>
          </section>
        </Reveal>

        <div aria-hidden className="h-[2.6cqw] border-t-[0.7cqw] border-[#b7a682] bg-[#d9c8a4]" />
      </div>
    </div>
  )
}
