import { createFileRoute } from '@tanstack/react-router'

import { Floor } from '../components/Floor'
import { Masthead } from '../components/Masthead'
import { Reveal } from '../components/Reveal'
import { Roof } from '../components/scenes/Roof'
import { profile } from '../content'

export const Route = createFileRoute('/work')({ component: Work })

/** A red sawtooth on marigold, as a tile: the border printed down the poster's left edge. */
const sawtooth =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 20' preserveAspectRatio='none'%3E%3Crect width='10' height='20' fill='%23f2b632'/%3E%3Cpath d='M0 0 10 10 0 20Z' fill='%23b3291b'/%3E%3C/svg%3E\")"

/**
 * Where I've worked, as the poster for a film about it. Under the masthead is a building cut open from the
 * roof to the street, with a floor for each job, the newest at the top. Everything on the sheet is sized off the sheet's width, so it scales as a print would, and the
 * sheet is no wider than lets the whole of it show at once: the page's own margins above and below are
 * given over to it. Where the page is too narrow for that, the rooms stack and the sheet scrolls.
 */
function Work() {
  const { experience, handle, nav } = profile
  const issue = nav.findIndex((item) => item.to === '/work') + 1

  return (
    <div className="@container/box w-full font-futura">
      <svg aria-hidden width="0" height="0" className="absolute">
        <defs>
          {/* Chalk on a board: a broken edge, the slate showing through where the stick skipped, and its dust. */}
          <filter id="chalk" x="-5%" y="-12%" width="110%" height="124%" colorInterpolationFilters="sRGB">
            <feTurbulence type="fractalNoise" baseFrequency="0.5" numOctaves="2" seed="4" result="edge" />
            <feDisplacementMap in="SourceGraphic" in2="edge" scale="3" xChannelSelector="R" yChannelSelector="G" result="rough" />
            <feTurbulence type="fractalNoise" baseFrequency="0.35 1.3" numOctaves="3" seed="9" result="grain" />
            <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3.2 0 0 0 -0.72" result="skips" />
            <feComposite in="rough" in2="skips" operator="in" result="stroke" />
            <feGaussianBlur in="rough" stdDeviation="1.8" result="cloud" />
            <feColorMatrix in="cloud" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.3 0" result="dust" />
            <feMerge>
              <feMergeNode in="dust" />
              <feMergeNode in="stroke" />
            </feMerge>
          </filter>
          <filter id="chalk-fine" x="-5%" y="-15%" width="110%" height="130%" colorInterpolationFilters="sRGB">
            <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" seed="6" result="edge" />
            <feDisplacementMap in="SourceGraphic" in2="edge" scale="1.5" xChannelSelector="R" yChannelSelector="G" result="rough" />
            <feTurbulence type="fractalNoise" baseFrequency="0.6 1.6" numOctaves="2" seed="12" result="grain" />
            <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3 0 0 0 -0.5" result="skips" />
            <feComposite in="rough" in2="skips" operator="in" result="stroke" />
            <feGaussianBlur in="rough" stdDeviation="1" result="cloud" />
            <feColorMatrix in="cloud" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.25 0" result="dust" />
            <feMerge>
              <feMergeNode in="dust" />
              <feMergeNode in="stroke" />
            </feMerge>
          </filter>
        </defs>
      </svg>
      <div className="@container mx-auto @md/box:-my-[4vh] @md/box:max-w-[80vh]">
        <div className="relative pl-[4.6cqw] text-[12px] leading-[1.4] @md/box:text-[2cqw]">
          <div
            aria-hidden
            className="absolute inset-y-0 left-0 w-[2.4cqw] bg-size-[100%_4.8cqw]"
            style={{ backgroundImage: sawtooth }}
          />

          <Reveal delay={0.1}>
            <Masthead presenter={handle} issue={issue} />
          </Reveal>

          <Reveal delay={0.3} className="mt-[2.5cqw] px-[2.5cqw]">
            <h2 className="sr-only">Experience</h2>
            <div className="-mx-[2.5cqw]">
              <Roof sign="Experience" />
            </div>
            <ol className="flex flex-col gap-[1.3cqw] border-t-[1cqw] border-cream bg-mendl p-[1.3cqw]">
              {experience.map((role, i) => (
                <li key={`${role.org}-${role.period}`}>
                  <Floor role={role} index={i} />
                </li>
              ))}
            </ol>
          </Reveal>

          <div aria-hidden className="h-[2.6cqw] border-t-[0.7cqw] border-[#b7a682] bg-[#d9c8a4]" />
        </div>
      </div>
    </div>
  )
}
