import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import { cv, profile } from '../content'
import BlurText from './bits/BlurText'
import VariableProximity from './bits/VariableProximity'

// One face, Archivo, at three widths, each with one job: widest for names (as the badge sets them), normal for
// reading, condensed for the dates, places and labels a reader runs an eye down.
const WIDE = '[font-stretch:125%]'
const NARROW = '[font-stretch:72%] tabular-nums tracking-[0.01em]'

const INK = 'text-[#1c1f1e]'
const GRAPHITE = 'text-[#5b605d]'
const LINK =
  'underline decoration-current/30 decoration-1 underline-offset-[0.22em] transition-[text-decoration-color] hover:decoration-current focus-visible:rounded-[2px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1c1f1e]'
const HEADING = `${WIDE} text-[1.5rem] leading-none font-[780] tracking-[-0.02em] print:text-[14pt]`

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

/** A point's text, with any of its marked phrases set in a highlighter swipe. */
function marked(text: string): ReactNode[] {
  const found = MARKS.filter((mark) => text.includes(mark))
  if (found.length === 0) return [text]
  const pattern = new RegExp(`(${found.map((mark) => mark.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`)
  return text.split(pattern).map((part, index) =>
    found.includes(part) ? (
      <mark
        key={index}
        className="bg-transparent bg-[linear-gradient(101deg,transparent_0.28em,rgb(247_234_72/0.95)_0.28em,rgb(243_228_68/0.8)_calc(100%-0.3em),transparent_calc(100%-0.3em))] bg-[length:100%_72%] bg-[position:0_58%] bg-no-repeat [box-decoration-break:clone] px-[0.22em] -mx-[0.12em] text-inherit print:[print-color-adjust:exact]"
      >
        {part}
      </mark>
    ) : (
      part
    ),
  )
}

/**
 * The résumé set as a page of text, word for word what resume.pdf says, so it can be searched, read aloud and copied
 * from. On a wide window the name runs down the left edge the way it is printed on the spine of the rolled résumé on
 * the desk, and stays there while the page scrolls; on a phone, and on paper, it heads the page. Its letters thin and
 * narrow on Archivo's own axes as a pointer passes over them (React Bits' Variable Proximity), and the headline comes
 * into focus a word at a time as the page opens (Blur Text), which is the page's only motion of its own.
 */
export function ResumePage() {
  const github = profile.socials.find((social) => social.label === 'GitHub')

  return (
    <div className={`min-h-screen bg-[#f3f4f1] text-[17px] leading-[1.62] ${INK} [font-stretch:100%] print:bg-white print:text-[9.5pt] print:leading-[1.5]`}>
      <div className="mx-auto max-w-[48rem] lg:grid lg:max-w-none lg:grid-cols-[auto_minmax(0,46rem)] lg:justify-center lg:gap-x-[clamp(3.5rem,7vw,7.5rem)] lg:px-10 print:block print:max-w-none">
        <nav className={`${GRAPHITE} flex justify-between gap-6 text-[0.88em] px-5 pt-6 sm:px-8 lg:col-start-2 lg:row-start-1 lg:px-0 lg:pt-10 print:hidden`}>
          <Link to="/" className={LINK}>
            Back to the site
          </Link>
          <a href={profile.resume.href} className={LINK}>
            Download the PDF
          </a>
        </nav>

        <div className="lg:col-start-1 lg:row-span-2 lg:row-start-1">
          <div className="lg:sticky lg:top-0 lg:flex lg:h-svh lg:items-center print:static print:block print:h-auto">
            <h1
              className={`${WIDE} px-5 pt-14 text-[calc((min(100vw,48rem)-2.5rem)/7.1)] sm:text-[calc((min(100vw,48rem)-4rem)/7.1)] leading-[0.84] font-[880] tracking-[-0.045em] whitespace-nowrap sm:px-8 lg:p-0 lg:text-[min(calc((100svh-4rem)/6.9),10rem)] lg:[writing-mode:vertical-rl] print:p-0 print:text-[40pt] print:leading-none print:[writing-mode:horizontal-tb]`}
            >
              <VariableProximity
                label={cv.name}
                fromFontVariationSettings="'wght' 880, 'wdth' 125"
                toFontVariationSettings="'wght' 220, 'wdth' 84"
                radius={170}
                falloff="gaussian"
              />
            </h1>
          </div>
        </div>

        <main className="px-5 pb-28 sm:px-8 lg:col-start-2 lg:row-start-2 lg:px-0 print:p-0">
          <header className="mt-6 border-b-[3px] border-current pb-6 lg:mt-[clamp(4rem,16vh,10rem)] print:mt-3 print:pb-3">
            <BlurText
              text={cv.headline}
              trigger="load"
              direction="bottom"
              delay={70}
              blur={8}
              distance={16}
              className={`${WIDE} text-[clamp(1.6rem,3.4vw,2.6rem)] leading-[1.05] font-[640] tracking-[-0.025em] print:text-[16pt]`}
            />
            <ul className={`${NARROW} mt-4 flex flex-wrap gap-x-7 gap-y-1 text-[1.12em] print:mt-2`}>
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
          </header>

          <section aria-labelledby="experience" className="mt-16 print:mt-6">
            <h2 id="experience" className={HEADING}>
              Experience
            </h2>
            <div className="mt-8 print:mt-3">
              {cv.roles.map((role) => (
                <article key={role.company} className="border-t border-current/15 py-9 first:border-t-0 first:pt-0 print:break-inside-avoid print:py-4">
                  <div className="grid items-baseline gap-x-6 sm:grid-cols-[minmax(0,1fr)_auto]">
                    <h3 className={`${WIDE} text-[1.32em] leading-tight font-[720] tracking-[-0.015em]`}>
                      <a href={role.href} className={LINK}>
                        {role.company}
                      </a>
                    </h3>
                    <p className={`${NARROW} ${GRAPHITE} text-[1.06em] max-sm:order-3 sm:text-right`}>{role.period}</p>
                    <p className="font-[560] max-sm:order-2">
                      {role.title}
                      {role.about && <span className={`${GRAPHITE} font-[450]`}>, {role.about}</span>}
                    </p>
                    <p className={`${NARROW} ${GRAPHITE} text-[1.06em] max-sm:order-4 sm:text-right`}>{role.place}</p>
                  </div>
                  <ul className="mt-5 max-w-[39rem] space-y-3.5 print:mt-2 print:max-w-none print:space-y-1.5">
                    {role.points.map((point) => (
                      <li key={point.slice(0, 32)} className="relative pl-6 before:absolute before:top-[0.8em] before:left-0 before:h-[2px] before:w-3 before:bg-current/45">
                        {marked(point)}
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </section>

          <section aria-labelledby="skills" className="mt-14 border-t-[3px] border-current pt-6 print:mt-5 print:break-inside-avoid print:pt-3">
            <h2 id="skills" className={HEADING}>
              Skills and interests
            </h2>
            <dl className="mt-7 grid gap-x-8 gap-y-4 sm:grid-cols-[10rem_minmax(0,39rem)] print:mt-3 print:grid-cols-[8rem_1fr] print:gap-y-1">
              {cv.skills.map((skill) => (
                <div key={skill.label} className="contents">
                  <dt className={`${NARROW} ${GRAPHITE} text-[1.06em] max-sm:mt-2`}>{skill.label}</dt>
                  <dd>{skill.value}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section aria-labelledby="education" className="mt-14 border-t-[3px] border-current pt-6 print:mt-5 print:break-inside-avoid print:pt-3">
            <h2 id="education" className={HEADING}>
              Education
            </h2>
            <div className="mt-7 grid gap-x-8 gap-y-5 sm:grid-cols-[10rem_minmax(0,39rem)] print:mt-3 print:grid-cols-[8rem_1fr] print:gap-y-1.5">
              {cv.education.map((school) => (
                <div key={school.course} className="contents">
                  <p className={`${NARROW} ${GRAPHITE} text-[1.06em] max-sm:mt-2`}>{school.grade}</p>
                  <div>
                    <p className="font-[600]">{school.course}</p>
                    <p className={GRAPHITE}>{school.school}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}
