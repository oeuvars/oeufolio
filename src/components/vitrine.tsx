import '@fontsource-variable/bodoni-moda/opsz.css'
import '@fontsource-variable/bodoni-moda/opsz-italic.css'

import { Link } from '@tanstack/react-router'
import { useEffect, useRef, useState, type ReactNode } from 'react'

import { cv, profile } from '../content'
import type { CvRole } from '../types'
import { GlassSurface } from './bits/glass-surface'
import { Silk } from './bits/silk'

// Claret silk under clear glass, and the type in ivory on it.
const CLARET = '#80263a'
const SHEEN = '#ffd6c4'
const DEEP = '#2a0a10'

const SERIF = "font-['Bodoni_Moda_Variable',serif] [font-optical-sizing:auto]"
const FOCUS = 'focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#f7f0ea]'
const LINK = `underline decoration-[#f7f0ea]/30 underline-offset-[5px] transition-colors hover:decoration-[#f7f0ea] ${FOCUS}`

// Silk measures its folds' relief across one pixel of the canvas, so a narrow window draws them steeper and glossier;
// a phone gets shallower, duller folds to come out the same.
const FOLDS = { wide: { sheen: 1.1, depth: 0.85, glow: 0.55 }, narrow: { sheen: 0.35, depth: 0.3, glow: 0.2 } }

const useNarrow = () => {
  const [narrow, setNarrow] = useState(false)
  useEffect(() => {
    const media = window.matchMedia('(max-width: 640px)')
    const update = () => setNarrow(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])
  return narrow
}

/** "March 2025 to now" as "Mar 2025 – Present". */
const period = (text: string) =>
  text
    .split(' to ')
    .map((part) => (part === 'now' ? 'Present' : `${part.slice(0, 3)} ${part.split(' ')[1]}`))
    .join(' – ')

/** A section: its name in italics in the left column, a hairline down beside it and across above it. */
const Section = ({ id, title, children }: { id: string; title: string; children: ReactNode }) => {
  return (
    <section aria-labelledby={id} className="grid border-t border-[#f7f0ea]/15 md:grid-cols-[10.5rem_1fr]">
      <h2 id={id} className={`${SERIF} pt-7 text-[22px] leading-none text-[#f7f0ea]/90 italic md:border-r md:border-[#f7f0ea]/15 md:pr-6`}>
        {title}
      </h2>
      <div className="min-w-0 pb-2 md:pl-8">{children}</div>
    </section>
  )
}

const Role = ({ role }: { role: CvRole }) => {
  return (
    <article className="border-t border-[#f7f0ea]/10 py-7 first:border-t-0">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <h3 className={`${SERIF} text-[26px] leading-tight font-medium`}>
          <a href={role.href} target="_blank" rel="noopener" className={`decoration-transparent hover:underline ${LINK}`}>
            {role.company}
          </a>
        </h3>
        <p className="text-[13px] tracking-[0.04em] text-[#f7f0ea]/60 tabular-nums">{period(role.period)}</p>
      </div>
      <p className="mt-1.5 text-[15px] text-[#f7f0ea]/70">
        {role.title}, {role.place === 'Remote' ? 'remote' : role.place}
      </p>
      <ul className="mt-4 max-w-[64ch] space-y-3 text-[15.5px] leading-[1.65] text-[#f7f0ea]/88">
        {role.points.map((point) => (
          <li key={point.slice(0, 32)} className="relative pl-5">
            <span aria-hidden="true" className="absolute top-[0.8em] left-0 h-px w-2.5 bg-[#f7f0ea]/50" />
            {point}
          </li>
        ))}
      </ul>
    </article>
  )
}

/**
 * The résumé behind glass: a single pane of React Bits' Glass Surface, edged and bordered, held over a field of claret
 * Silk that unfurls when the page opens. The pane stays put and the résumé scrolls inside it, word for word what
 * resume.pdf says.
 */
export const Vitrine = () => {
  const city = profile.extras.particulars.find((particular) => particular.label === 'Based in')?.value ?? ''
  const folds = useNarrow() ? FOLDS.narrow : FOLDS.wide
  const pane = useRef<HTMLElement>(null)

  // The page itself never scrolls, so the pane takes focus at once and the keyboard's scroll keys move it.
  useEffect(() => pane.current?.focus({ preventScroll: true }), [])

  return (
    <div className="h-dvh w-full overflow-hidden font-['Jost_Variable',sans-serif] text-[#f7f0ea] antialiased" style={{ backgroundColor: DEEP, colorScheme: 'dark' }}>
      <div aria-hidden="true" className="fixed inset-0">
        <Silk color={CLARET} sheenColor={SHEEN} speed={2} scale={1.35} rotation={0.35} {...folds} noiseIntensity={0.5} mouseInteraction={false} clickRipple={false} />
      </div>

      <div className="fixed inset-x-0 inset-y-[10px] mx-auto w-[calc(100%-20px)] max-w-[920px] sm:inset-y-6 sm:w-[calc(100%-48px)]">
        <GlassSurface width="100%" height="100%" borderRadius={30} borderWidth={0.05} blur={14} displace={12} backgroundOpacity={0.2} saturation={1.15} distortionScale={-90} className="!p-0">
          <div className="relative h-full w-full overflow-hidden rounded-[22px] border border-[#f7f0ea]/25 bg-[#2a0a10]/55 sm:bg-[#2a0a10]/15">
            <main
              ref={pane}
              tabIndex={-1}
              className="h-full overflow-y-auto overscroll-contain px-5 pt-10 pb-12 outline-none [mask-image:linear-gradient(transparent,#000_28px,#000_calc(100%-28px),transparent)] sm:px-12 sm:pt-14"
            >
              <header className="pb-10">
                <h1 className={`${SERIF} text-[clamp(52px,10vw,104px)] leading-[0.92] font-normal tracking-[-0.015em]`}>{cv.name}</h1>
                <p lang="hi" className="mt-4 text-[19px] text-[#f7f0ea]/70">
                  अनुराग दास
                </p>
                <p className="mt-1 text-[17px] text-[#f7f0ea]/85">
                  {cv.headline}, in {city}
                </p>
                <div className="mt-8 flex flex-wrap items-center justify-between gap-x-8 gap-y-5">
                  <div className="flex flex-wrap gap-3">
                    <a
                      href={profile.resume.href}
                      target="_blank"
                      rel="noopener"
                      className={`rounded-full bg-[#f7f0ea] px-5 py-2.5 text-[14px] font-medium text-[#3a0f15] transition-colors hover:bg-white ${FOCUS}`}
                    >
                      Download the PDF
                    </a>
                    <a
                      href={`mailto:${profile.email}`}
                      className={`rounded-full border border-[#f7f0ea]/45 px-5 py-2.5 text-[14px] font-medium transition-colors hover:border-[#f7f0ea] hover:bg-[#f7f0ea]/10 ${FOCUS}`}
                    >
                      {profile.email}
                    </a>
                  </div>
                  <nav aria-label="Profiles" className="flex gap-6 text-[14px]">
                    {profile.socials.map((social) => (
                      <a key={social.label} href={social.href} target="_blank" rel="noopener" className={LINK}>
                        {social.label}
                      </a>
                    ))}
                  </nav>
                </div>
              </header>

              <Section id="experience" title="Experience">
                {cv.roles.map((role) => (
                  <Role key={role.company} role={role} />
                ))}
              </Section>

              <Section id="skills" title="Skills">
                <dl className="grid max-w-[64ch] gap-x-6 gap-y-3 py-7 sm:grid-cols-[10rem_1fr]">
                  {cv.skills.map((skill) => (
                    <div key={skill.label} className="contents">
                      <dt className="pt-[2px] text-[13px] tracking-[0.02em] text-[#f7f0ea]/60">{skill.label}</dt>
                      <dd className="-mt-2 text-[15.5px] leading-[1.55] text-[#f7f0ea]/88 sm:mt-0">{skill.value}</dd>
                    </div>
                  ))}
                </dl>
              </Section>

              <Section id="education" title="Education">
                {cv.education.map((school) => (
                  <div key={school.school} className="border-t border-[#f7f0ea]/10 py-7 first:border-t-0">
                    <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
                      <h3 className={`${SERIF} text-[22px] leading-tight font-medium`}>{school.school}</h3>
                      <p className="text-[13px] tracking-[0.04em] text-[#f7f0ea]/60 tabular-nums">{school.grade}</p>
                    </div>
                    <p className="mt-1.5 text-[15px] text-[#f7f0ea]/70">{school.course}</p>
                  </div>
                ))}
              </Section>

              <footer className="flex justify-center border-t border-[#f7f0ea]/15 pt-8">
                <Link to="/" className={`text-[14px] ${LINK}`}>
                  Back to the site
                </Link>
              </footer>
            </main>
          </div>
        </GlassSurface>
      </div>
    </div>
  )
}
