import type { ReactNode } from 'react'

import { cv, profile } from '../../content'
import type { CvRole } from '../../types'
import Counter from '../bits/Counter'

/** "March 2025 to now" as "Mar 2025 – now". */
const period = (text: string) =>
  text
    .split(' to ')
    .map((part) => (part === 'now' ? 'now' : `${part.slice(0, 3)} ${part.split(' ')[1]}`))
    .join(' – ')

/** The résumé's three figures, highlighted where its points give them, each rolling in on a counter when first seen. */
const FIGURES: { text: string; value: number; decimals?: number; suffix: string; rest: string }[] = [
  { text: '50,000+ rule executions', value: 50000, suffix: '+', rest: ' rule executions' },
  { text: '10,000+ label generations', value: 10000, suffix: '+', rest: ' label generations' },
  { text: '99.9% uptime', value: 99.9, decimals: 1, suffix: '%', rest: ' uptime' },
]

const MARK =
  'bg-[linear-gradient(transparent_12%,#f5e34a_12%,#f5e34a_88%,transparent_88%)] px-[0.15em] font-semibold text-black [box-decoration-break:clone] print:[print-color-adjust:exact]'

function marked(point: string) {
  const parts: ReactNode[] = []
  let rest = point
  for (;;) {
    const hits = FIGURES.map((figure) => ({ figure, at: rest.indexOf(figure.text) })).filter((hit) => hit.at >= 0)
    if (!hits.length) break
    const { figure, at } = hits.reduce((a, b) => (b.at < a.at ? b : a))
    parts.push(rest.slice(0, at))
    parts.push(
      <mark key={figure.text} className={MARK}>
        <Counter value={figure.value} decimals={figure.decimals} suffix={figure.suffix} fontSize="1em" fade={0.15} duration={0.9} stagger={0.06} />
        {figure.rest}
      </mark>,
    )
    rest = rest.slice(at + figure.text.length)
  }
  parts.push(rest)
  return parts
}

/** A section's head: white on a black bar, the reverse print a label uses for its service line. */
function Bar({ id, children }: { id: string; children: ReactNode }) {
  return (
    <div className="rounded-[2px] bg-black px-3 py-1.5 text-white print:[print-color-adjust:exact]">
      <h2 id={id} className="text-[14px] leading-none font-bold [font-stretch:112%]">
        {children}
      </h2>
    </div>
  )
}

function Role({ role }: { role: CvRole }) {
  const remote = role.place === 'Remote'
  return (
    <li className="border-t border-black/15 py-6 first:border-t-0">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <h3 className="text-[21px] leading-tight font-extrabold tracking-[-0.01em] [font-stretch:112%]">
          <a href={role.href} target="_blank" rel="noopener" className="underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black">
            {role.company}
          </a>
        </h3>
        <p className="text-[14px] font-semibold tabular-nums [font-stretch:80%]">{period(role.period)}</p>
      </div>
      <p className="mt-1 text-[16px] text-black/70">
        {role.title}, {remote ? 'remote' : role.place}
        {role.about && <span className="text-black/55">. {role.about}</span>}
      </p>
      <ul className="mt-4 space-y-3 text-[16px] leading-[1.6]">
        {role.points.map((point) => (
          <li key={point.slice(0, 32)} className="relative pl-5">
            <span aria-hidden="true" className="absolute top-[0.62em] left-0.5 size-[6px] bg-black" />
            {marked(point)}
          </li>
        ))}
      </ul>
    </li>
  )
}

/**
 * The packing slip that comes with the label: the résumé in full, word for word what resume.pdf says. Its sections
 * open on black bars, and its figures are highlighted.
 */
export function Slip() {
  const coursework = cv.skills.find((skill) => skill.label === 'Relevant coursework')
  const skills = cv.skills.filter((skill) => skill !== coursework)
  const button =
    'inline-flex items-center rounded-[3px] px-4 py-2.5 text-[14px] leading-none font-bold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black'

  return (
    <article aria-labelledby="slip-title" className="bg-white px-5 pt-8 pb-10 text-black sm:px-10 sm:pt-10 print:p-0">
      <header className="max-w-[62ch]">
        <p id="slip-title" className="text-[30px] leading-none font-black tracking-[-0.02em] [font-stretch:112%]">
          Packing slip
        </p>
        <p className="mt-4 text-[18px] leading-[1.5]">
          Full stack developer. I build the software warehouses ship with: automation engines, packing-station apps and shipping labels.
        </p>
        <div className="mt-6 flex flex-wrap gap-2 print:hidden">
          <a href={profile.resume.href} target="_blank" rel="noopener" className={`${button} bg-black text-white hover:bg-black/80`}>
            Download the PDF
          </a>
          <a href={`mailto:${profile.email}`} className={`${button} shadow-[inset_0_0_0_2px_black] hover:bg-black hover:text-white`}>
            Email me
          </a>
        </div>
      </header>

      <section aria-labelledby="roles" className="mt-10">
        <Bar id="roles">
          Roles
        </Bar>
        <ul className="max-w-[62ch]">
          {cv.roles.map((role) => (
            <Role key={role.company} role={role} />
          ))}
        </ul>
      </section>

      <section aria-labelledby="skills" className="mt-6">
        <Bar id="skills">Skills</Bar>
        <dl className="mt-5 grid max-w-[62ch] gap-x-6 gap-y-4 sm:grid-cols-[11rem_1fr]">
          {skills.map((skill) => (
            <div key={skill.label} className="contents">
              <dt className="text-[14px] font-bold [font-stretch:80%] sm:pt-[3px]">{skill.label}</dt>
              <dd className="-mt-3 text-[16px] leading-[1.5] sm:mt-0">{skill.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="schooling" className="mt-10">
        <Bar id="schooling">Schooling</Bar>
        <ul className="max-w-[62ch]">
          {cv.education.map((school) => (
            <li key={school.school} className="border-t border-black/15 py-5 first:border-t-0">
              <div className="flex flex-wrap items-baseline justify-between gap-x-6">
                <h3 className="text-[18px] font-extrabold [font-stretch:112%]">{school.school}</h3>
                <p className="text-[14px] font-semibold tabular-nums [font-stretch:80%]">{school.grade}</p>
              </div>
              <p className="mt-1 text-[16px] text-black/70">{school.course}</p>
              {school === cv.education[0] && coursework && <p className="mt-2 text-[14px] leading-[1.5] text-black/60">Coursework: {coursework.value}</p>}
            </li>
          ))}
        </ul>
      </section>
    </article>
  )
}
