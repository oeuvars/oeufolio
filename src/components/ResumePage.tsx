import { Link } from '@tanstack/react-router'
import type { CSSProperties, ReactNode } from 'react'

import { cv, profile } from '../content'
import BlurText from './bits/BlurText'
import TiltedCard from './bits/TiltedCard'
import VariableProximity from './bits/VariableProximity'

// One face, Archivo, at three widths, each with one job: widest for names (as the badge sets them), normal for
// reading, condensed for the dates, places and labels a reader runs an eye down.
const WIDE = '[font-stretch:125%]'
const NARROW = '[font-stretch:72%] tabular-nums tracking-[0.01em]'

const GRAPHITE = 'text-[#5b605d]'
const LINK =
  'underline decoration-current/30 decoration-1 underline-offset-[0.22em] transition-[text-decoration-color] hover:decoration-current focus-visible:rounded-[2px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1c1f1e]'
const HEADING = `${WIDE} border-t-[3px] border-current pt-5 text-[1.6rem] leading-none font-[780] tracking-[-0.02em] print:pt-3 print:text-[14pt]`

/**
 * Each employer's colour, taken from the site's own surfaces: the steel plate the badge hangs on, the green cutting
 * mat, the maroon folder the résumé roll lies by. The ruler's spans and each role's heading share it, so a span on the
 * ruler reads as the role below it.
 */
const COLOURS: Record<string, string> = {
  'Cybership.io': '#4b6d69',
  'Ekarth Ventures': '#2f5e45',
  'DataVerse India': '#6a2420',
}

/**
 * The figures a reader is looking for, swiped with a highlighter where each point says them. A phrase has to appear
 * in its point word for word, or it is left unmarked.
 */
const MARKS = [
  '50,000+ rule executions',
  '64 protocol decoders',
  'often the same day',
  '10,000+ label generations daily',
  '99.9% uptime',
  '10-fold (2.2 GB to 178 MB)',
]

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

/** "March 2025" as a count of months, or this month for "now". */
function month(text: string): number {
  const today = new Date()
  if (text === 'now') return today.getFullYear() * 12 + today.getMonth()
  const [name, year] = text.split(' ')
  return Number(year) * 12 + MONTHS.indexOf(name)
}

/** A role's period, "March 2025 to now", as the months it starts and ends on. */
function span(period: string) {
  const [from, to] = period.split(' to ')
  return { from: month(from), to: month(to) }
}

const anchor = (company: string) => company.toLowerCase().replace(/[^a-z]+/g, '-')

/** A point's text, with any of its marked phrases set in a highlighter swipe. */
function marked(text: string): ReactNode[] {
  const found = MARKS.filter((mark) => text.includes(mark))
  if (found.length === 0) return [text]
  const pattern = new RegExp(`(${found.map((mark) => mark.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`)
  return text.split(pattern).map((part, index) =>
    found.includes(part) ? (
      <mark
        key={index}
        className="-mx-[0.12em] bg-transparent bg-[linear-gradient(101deg,transparent_0.28em,rgb(247_234_72/0.95)_0.28em,rgb(243_228_68/0.8)_calc(100%-0.3em),transparent_calc(100%-0.3em))] bg-[length:100%_72%] bg-[position:0_58%] bg-no-repeat [box-decoration-break:clone] px-[0.22em] text-inherit print:[print-color-adjust:exact]"
      >
        {part}
      </mark>
    ) : (
      part
    ),
  )
}

/**
 * The career to scale: one tick a month from the first job to this month, a taller one at each new year, and each
 * role's months filled in its employer's colour. Each span links down to its role.
 */
function Ruler() {
  // A role that ends in the month the next one starts gives that month to the next one.
  const months = cv.roles.map((role) => span(role.period))
  const spans = cv.roles.map((role, i) => {
    const { from, to } = months[i]
    return { role, from, to: months.some((other) => other.from === to) ? to - 1 : to }
  }).sort((a, b) => a.from - b.from)
  const start = Math.min(...spans.map((s) => s.from))
  const end = Math.max(...spans.map((s) => s.to)) + 1
  const total = end - start
  const at = (m: number) => `${((m - start) / total) * 100}%`
  const ticks = Array.from({ length: total + 1 }, (_, i) => start + i)

  return (
    <figure className="@container mt-14 md:mt-20 print:mt-6 print:[print-color-adjust:exact]">
      <figcaption className="sr-only">{spans.map(({ role }) => `${role.company}, ${role.period}`).join('; ')}</figcaption>
      <div className="relative h-14 @4xl:h-16">
        {spans.map(({ role, from, to }) => (
          <a
            key={role.company}
            href={`#${anchor(role.company)}`}
            aria-label={role.company}
            className="group absolute inset-y-0 flex items-end overflow-hidden border-r-2 border-[#f3f4f1] px-2.5 pb-2 text-[#f3f4f1] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1c1f1e]"
            style={{ left: at(from), width: `calc(${at(to + 1)} - ${at(from)})`, backgroundColor: COLOURS[role.company] }}
          >
            <span className={`${WIDE} hidden truncate text-[0.95em] leading-none font-[680] tracking-[-0.01em] group-hover:underline @4xl:block`}>{role.company}</span>
          </a>
        ))}
      </div>
      <div aria-hidden="true" className="relative h-9">
        {ticks.map((m) => {
          const january = m % 12 === 0
          return (
            <span key={m} className="absolute top-0" style={{ left: at(m) }}>
              <span className={`block w-px bg-[#1c1f1e] ${january ? 'h-4' : 'h-2 opacity-40'}`} />
              {january && <span className={`${NARROW} ${GRAPHITE} absolute top-4 left-1.5 text-[0.9em]`}>{m / 12}</span>}
            </span>
          )
        })}
      </div>
      <ul aria-hidden="true" className={`${NARROW} mt-1 flex flex-wrap gap-x-6 gap-y-1 text-[0.95em] @4xl:hidden`}>
        {spans.map(({ role }) => (
          <li key={role.company} className="flex items-center gap-2">
            <span className="size-2.5" style={{ backgroundColor: COLOURS[role.company] }} />
            {role.company}
          </li>
        ))}
      </ul>
    </figure>
  )
}

/**
 * The résumé set as a page of text, word for word what resume.pdf says, so it can be searched, read aloud and copied
 * from. It opens the way the site does, with the name beside the badge hanging on its steel plate (both are the site's
 * own renders). Then the career runs to scale on a ruler, and each role follows, with its employer, dates and place
 * held beside its points.
 *
 * Three React Bits pieces move it, each only when asked: the badge tilts toward the pointer (Tilted Card), the name's
 * letters thin and narrow on Archivo's own axes as the pointer passes (Variable Proximity), and the headline comes into
 * focus a word at a time as the page opens (Blur Text).
 */
export function ResumePage() {
  const github = profile.socials.find((social) => social.label === 'GitHub')

  return (
    <div className="min-h-screen bg-[#f3f4f1] text-[17px] leading-[1.62] text-[#1c1f1e] [font-stretch:100%] print:bg-white print:text-[9.5pt] print:leading-[1.5]">
      <header className="grid lg:min-h-[min(100svh,64rem)] lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] print:block print:min-h-0">
        <div className="flex flex-col px-5 pt-6 pb-12 sm:px-10 lg:px-14 lg:pt-8 lg:pb-14 print:p-0">
          <nav className={`${GRAPHITE} text-[0.88em] print:hidden`}>
            <Link to="/" className={LINK}>
              Back to the site
            </Link>
          </nav>

          <div className="mt-12 lg:mt-auto print:mt-0">
            <h1 className={`${WIDE} text-[min(17.5vw,8rem)] leading-[0.86] font-[880] tracking-[-0.045em] lg:text-[min(9.6vw,10.5rem)] print:text-[40pt] print:leading-none`}>
              <VariableProximity
                label={cv.name}
                fromFontVariationSettings="'wght' 880, 'wdth' 125"
                toFontVariationSettings="'wght' 200, 'wdth' 80"
                radius={190}
                falloff="gaussian"
              />
            </h1>
            <BlurText
              text={cv.headline}
              trigger="load"
              direction="bottom"
              delay={70}
              blur={8}
              distance={16}
              className={`${WIDE} mt-6 text-[clamp(1.4rem,2.6vw,2.2rem)] leading-[1.08] font-[620] tracking-[-0.02em] print:mt-2 print:text-[15pt]`}
            />
            <ul className={`${NARROW} mt-5 flex flex-wrap gap-x-7 gap-y-1 text-[1.12em] print:mt-2`}>
              <li>
                <a href={`mailto:${profile.email}`} className={LINK}>
                  {profile.email}
                </a>
              </li>
              {github && (
                <li>
                  <a href={github.href} className={LINK}>
                    {github.href.replace('https://', '')}
                  </a>
                </li>
              )}
            </ul>
            <a
              href={profile.resume.href}
              className="mt-9 inline-block bg-[#1c1f1e] px-5 py-3 text-[0.95em] font-[600] text-[#f3f4f1] transition-colors hover:bg-[#4b6d69] focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-[#1c1f1e] print:hidden"
            >
              Download the PDF
            </a>
          </div>
        </div>

        <div className="relative h-[min(125vw,40rem)] overflow-hidden bg-[#5d7a76] bg-[url(/objects/steel.avif)] bg-cover bg-center [container-type:size] lg:h-auto print:hidden">
          <TiltedCard
            containerWidth="100%"
            containerHeight="100%"
            imageHeight="min(94cqh, 117.5cqw)"
            imageWidth="min(75.2cqh, 94cqw)"
            className="!items-start"
            radius={0}
            rotateAmplitude={9}
            scaleOnHover={1.02}
            glare={0}
            shadow={0}
            parallax={0}
            showTooltip={false}
            flipOnClick={false}
            gyroscope={false}
            style={{ '--tc-rim-color': 'transparent', '--tc-rim-light': 'transparent' } as CSSProperties}
          >
            <img
              src={profile.badge.src}
              alt={profile.badge.alt}
              draggable={false}
              className="pointer-events-none absolute inset-x-[3%] top-0 h-[96%] w-[94%] object-contain object-top [filter:drop-shadow(0_10px_14px_rgb(0_0_0/0.3))]"
            />
          </TiltedCard>
        </div>
      </header>

      <main className="mx-auto max-w-[76rem] px-5 pb-28 sm:px-10 lg:px-14 print:max-w-none print:p-0 print:pb-0">
        <Ruler />

        <section aria-labelledby="experience" className="mt-16 md:mt-24 print:mt-6">
          <h2 id="experience" className={HEADING}>
            Experience
          </h2>
          {cv.roles.map((role) => (
            <article
              key={role.company}
              id={anchor(role.company)}
              className="mt-10 grid scroll-mt-8 gap-x-14 gap-y-5 border-t border-current/15 pt-10 first-of-type:border-t-0 first-of-type:pt-0 md:mt-14 md:grid-cols-[17rem_minmax(0,1fr)] md:pt-14 lg:grid-cols-[21rem_minmax(0,1fr)] print:mt-4 print:grid-cols-[12rem_1fr] print:break-inside-avoid print:pt-4"
            >
              <div className="self-start md:sticky md:top-8 print:static">
                <span className="block h-1.5 w-14 print:[print-color-adjust:exact]" style={{ backgroundColor: COLOURS[role.company] }} />
                <h3 className={`${WIDE} mt-4 text-[1.45em] leading-[1.1] font-[740] tracking-[-0.015em]`}>
                  <a href={role.href} className={LINK}>
                    {role.company}
                  </a>
                </h3>
                {role.about && <p className={`${GRAPHITE} mt-1`}>{role.about}</p>}
                <p className="mt-3 font-[600]">{role.title}</p>
                <p className={`${NARROW} ${GRAPHITE} text-[1.06em]`}>
                  {role.period}
                  <br />
                  {role.place}
                </p>
              </div>
              <ul className="max-w-[40rem] space-y-4 md:pt-1 print:max-w-none print:space-y-1.5">
                {role.points.map((point) => (
                  <li key={point.slice(0, 32)} className="relative pl-6 before:absolute before:top-[0.8em] before:left-0 before:h-[2px] before:w-3 before:bg-current/45">
                    {marked(point)}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </section>

        <section aria-labelledby="skills" className="mt-20 md:mt-28 print:mt-6 print:break-inside-avoid">
          <h2 id="skills" className={HEADING}>
            Skills and interests
          </h2>
          <dl className="mt-8 grid gap-x-14 gap-y-7 sm:grid-cols-2 lg:grid-cols-3 print:mt-3 print:grid-cols-3 print:gap-y-2">
            {cv.skills.map((skill) => (
              <div key={skill.label}>
                <dt className={`${NARROW} ${GRAPHITE} text-[1.06em]`}>{skill.label}</dt>
                <dd className="mt-0.5">{skill.value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section aria-labelledby="education" className="mt-20 md:mt-28 print:mt-6 print:break-inside-avoid">
          <h2 id="education" className={HEADING}>
            Education
          </h2>
          <div className="mt-8 grid gap-x-14 gap-y-7 sm:grid-cols-2 print:mt-3 print:gap-y-2">
            {cv.education.map((school) => (
              <div key={school.course}>
                <p className={`${NARROW} ${GRAPHITE} text-[1.06em]`}>{school.grade}</p>
                <p className="mt-0.5 font-[600]">{school.course}</p>
                <p className={GRAPHITE}>{school.school}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
