import { Link } from '@tanstack/react-router'

import { cv, profile } from '../content'

// The left-hand column on a wide page: dates and places beside a job, a skill's name beside the skill.
const ROW = 'grid gap-x-10 gap-y-1 md:grid-cols-[10.5rem_minmax(0,1fr)] print:grid-cols-[8.5rem_minmax(0,1fr)]'
const ASIDE = 'text-[0.9em] leading-[1.55] text-[#6b6860] tabular-nums'
const HEADING = 'mb-7 text-[1.3rem] leading-none font-[750] tracking-[-0.01em] [font-stretch:125%] print:mb-4 print:text-[13pt]'
const LINK = 'underline decoration-[#1d1d1b]/30 decoration-1 underline-offset-[0.22em] transition-colors hover:decoration-[#1d1d1b] focus-visible:rounded-[2px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1d1d1b]'

/**
 * The résumé set as a page of text, word for word what resume.pdf says, so it can be searched, read aloud and
 * copied from. It is one face, Archivo, at two widths: its widest for the name and the headings, as the badge sets
 * its type, and its normal width for everything read.
 */
export function ResumePage() {
  const github = profile.socials.find((social) => social.label === 'GitHub')

  return (
    <div className="min-h-screen bg-[#fbfaf6] text-[16.5px] leading-[1.6] text-[#1d1d1b] [font-stretch:100%] print:bg-white print:text-[10pt]">
      <div className="mx-auto max-w-[58rem] px-6 pt-8 pb-24 md:px-12 md:pt-10 print:max-w-none print:p-0">
        <nav className="flex justify-between gap-6 text-[0.9em] text-[#6b6860] print:hidden">
          <Link to="/" className={LINK}>
            Back to the site
          </Link>
          <a href={profile.resume.href} className={LINK}>
            Download the PDF
          </a>
        </nav>

        <header className="mt-16 md:mt-24 print:mt-0">
          <h1 className="text-[clamp(2.9rem,9vw,6.4rem)] leading-[0.88] font-[850] tracking-[-0.04em] [font-stretch:125%] print:text-[34pt]">{cv.name}</h1>
          <div className={`${ROW} mt-6 md:mt-8`}>
            <p className="md:col-start-2 text-[1.15em] font-[550]">{cv.headline}</p>
            <ul className="flex flex-wrap gap-x-6 gap-y-1 md:col-start-2">
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
          </div>
        </header>

        <section aria-labelledby="experience" className="mt-20 md:mt-28 print:mt-8">
          <h2 id="experience" className={HEADING}>
            Experience
          </h2>
          <div className="space-y-14 print:space-y-6">
            {cv.roles.map((role) => (
              <article key={role.company} className={ROW}>
                <p className={`${ASIDE} md:pt-[0.15em]`}>
                  {role.period}
                  <br />
                  {role.place}
                </p>
                <div className="max-w-[40rem]">
                  <h3 className="text-[1.08em] font-[650]">
                    <a href={role.href} className={LINK}>
                      {role.company}
                    </a>
                    {role.about && <span className="font-[400] text-[#6b6860]">, {role.about}</span>}
                  </h3>
                  <p className="text-[#3d3b37]">{role.title}</p>
                  <ul className="mt-4 space-y-3 print:mt-2 print:space-y-1.5">
                    {role.points.map((point) => (
                      <li key={point.slice(0, 32)} className="relative pl-5 before:absolute before:top-[0.78em] before:left-0 before:h-px before:w-2.5 before:bg-[#1d1d1b]/50">
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section aria-labelledby="skills" className="mt-20 md:mt-28 print:mt-8">
          <h2 id="skills" className={HEADING}>
            Skills and interests
          </h2>
          <dl className="space-y-4 print:space-y-1.5">
            {cv.skills.map((skill) => (
              <div key={skill.label} className={ROW}>
                <dt className={ASIDE}>{skill.label}</dt>
                <dd className="max-w-[40rem]">{skill.value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section aria-labelledby="education" className="mt-20 md:mt-28 print:mt-8">
          <h2 id="education" className={HEADING}>
            Education
          </h2>
          <div className="space-y-6 print:space-y-2">
            {cv.education.map((school) => (
              <div key={school.course} className={ROW}>
                <p className={ASIDE}>{school.grade}</p>
                <div>
                  <p className="font-[650]">{school.course}</p>
                  <p className="text-[#3d3b37]">{school.school}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
