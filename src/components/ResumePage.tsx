import '@fontsource-variable/geist'
import '@fontsource-variable/geist-mono'

import { Link } from '@tanstack/react-router'
import { useEffect, useId, useState, type CSSProperties, type ReactNode } from 'react'

import { cv, profile } from '../content'

// The page's two themes as variables, so one set of classes serves both.
const LIGHT = {
  '--page': '#ffffff',
  '--ink': '#18181b',
  '--body': '#52525b',
  '--muted': '#71717a',
  '--faint': '#a1a1aa',
  '--rule': '#a1a1aa',
  '--line': '#e4e4e7',
  '--chip': '#fafafa',
  '--chip-line': 'rgb(0 0 0 / 0.3)',
  '--hover': '#f4f4f5',
  '--button': '#18181b',
  '--button-ink': '#fafafa',
} as CSSProperties

const DARK = {
  '--page': '#000000',
  '--ink': '#f4f4f5',
  '--body': '#d4d4d8',
  '--muted': '#a1a1aa',
  '--faint': '#52525b',
  '--rule': '#52525b',
  '--line': '#27272a',
  '--chip': '#0a0a0a',
  '--chip-line': 'rgb(255 255 255 / 0.25)',
  '--hover': '#121214',
  '--button': '#fafafa',
  '--button-ink': '#18181b',
} as CSSProperties

const LOGOS: Record<string, string> = {
  'Cybership.io': '/objects/resume/cybership.png',
  'Ekarth Ventures': '/objects/resume/ekarth.png',
  'DataVerse India': '/objects/resume/dataverse.png',
}

const SECTIONS = [
  { id: 'experience', label: 'Experience' },
  { id: 'skills', label: 'Skills' },
  { id: 'education', label: 'Education' },
]

const FOCUS = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--ink)'
const MONO = "font-['Geist_Mono_Variable',ui-monospace,monospace]"
const LABEL = `${MONO} text-[10px] font-medium tracking-wider text-(--faint) uppercase`
const CHIP = `flex items-center gap-1.5 rounded-[4px] border border-(--line) bg-(--chip) px-3 py-1.5 text-[12px] font-medium text-(--body) transition-colors hover:bg-(--hover) hover:text-(--ink) ${FOCUS}`
const STAMP = `rounded-[4px] border border-(--line) bg-(--chip) px-3 py-1.5 ${MONO} text-[10px] tracking-[0.12em] text-(--muted) uppercase transition-colors hover:bg-(--hover) hover:text-(--ink) ${FOCUS}`
// Dotted rules as the reference draws them: a one-pixel dot every four pixels, sparser than CSS's own dotted border.
const DOTS_X = 'bg-[linear-gradient(to_right,var(--rule)_1px,transparent_1px)] bg-[length:4px_1px] bg-repeat-x'
const DOTS_Y = 'bg-[linear-gradient(to_bottom,var(--rule)_1px,transparent_1px)] bg-[length:1px_4px] bg-repeat-y'
const DOT = 'relative before:absolute before:top-[0.75em] before:-left-3 before:size-[3px] before:rounded-full before:bg-current'

const home = profile.extras.particulars.find((particular) => particular.label === 'Based in')?.value ?? ''

/** "March 2025 to now" as "Mar 2025 - Present". */
const period = (text: string) =>
  text
    .split(' to ')
    .map((part) => (part === 'now' ? 'Present' : `${part.slice(0, 3)} ${part.split(' ')[1]}`))
    .join(' - ')

function Icon({ children, fill = false }: { children: ReactNode; fill?: boolean }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="size-3.5 shrink-0"
      fill={fill ? 'currentColor' : 'none'}
      stroke={fill ? 'none' : 'currentColor'}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {children}
    </svg>
  )
}

const ICONS: Record<string, ReactNode> = {
  GitHub: (
    <Icon>
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </Icon>
  ),
  X: (
    <Icon fill>
      <path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.4l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.6l5.24 6.93Zm-1.29 19.5h2.04L6.49 3.24H4.3Z" />
    </Icon>
  ),
  Instagram: (
    <Icon>
      <rect width="20" height="20" x="2" y="2" rx="5" />
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
      <path d="M17.5 6.5h.01" />
    </Icon>
  ),
  Résumé: (
    <Icon>
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
      <path d="M14 2v4a2 2 0 0 0 2 2h4M16 13H8M16 17H8M10 9H8" />
    </Icon>
  ),
  mail: (
    <Icon>
      <rect width="20" height="16" x="2" y="4" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </Icon>
  ),
  download: (
    <Icon>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
    </Icon>
  ),
}

/** A rule run the whole width of the window, through the column's rails. */
const Rule = () => <div aria-hidden="true" className={`relative left-1/2 h-px w-screen -translate-x-1/2 ${DOTS_X} print:hidden`} />

/** A section's name, set between two rules. */
function Heading({ id, children }: { id: string; children: ReactNode }) {
  return (
    <>
      <Rule />
      <h2 id={id} className="scroll-mt-6 px-4 py-2 text-[18px] leading-[27px] font-bold tracking-tight text-(--ink)">
        {children}
      </h2>
      <Rule />
    </>
  )
}

/** One job: its logo, employer, title, dates and place, opening on its points. */
function Role({ role }: { role: (typeof cv.roles)[number] }) {
  const [open, setOpen] = useState(false)
  const panel = useId()
  const remote = role.place === 'Remote'

  return (
    <article className={`pb-px ${DOTS_X} bg-bottom last:bg-none last:pb-0`}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panel}
        onClick={() => setOpen(!open)}
        className={`block w-full px-4 py-4 text-left transition-colors hover:bg-(--hover) ${open ? 'bg-(--hover)' : ''} ${FOCUS} print:py-2`}
      >
        <span className="flex items-start gap-3 sm:gap-4">
          <span className="grid size-10 shrink-0 place-items-center rounded-lg border border-(--line) bg-white shadow-[0_1px_2px_rgb(0_0_0/0.06)]">
            <img src={LOGOS[role.company]} alt="" className="size-8 rounded-md object-contain" />
          </span>
          <span className="flex min-w-0 flex-col gap-0.5">
            <span className="flex flex-wrap items-center gap-2">
              <span className="text-[14px] leading-tight font-bold text-(--ink) sm:text-[17px]">{role.company}</span>
              {remote && <span className="rounded-[4px] border border-(--line) bg-(--hover) px-1.5 py-px text-[11px] font-medium text-(--body)">Remote</span>}
            </span>
            <span className="text-[14px] text-(--body) sm:text-[15px]">
              {role.title}
              {role.about && <span className="text-(--muted)">, {role.about}</span>}
            </span>
          </span>
        </span>
        <span className="mt-3 flex flex-col items-start gap-0.5 pl-[52px] sm:pl-[56px]">
          <span className="flex items-center gap-1 text-[13px] font-medium text-(--ink) sm:text-[14px]">
            {period(role.period)}
            <svg
              aria-hidden="true"
              viewBox="0 0 24 24"
              className={`size-3.5 transition-transform duration-300 motion-reduce:transition-none ${open ? 'rotate-180' : ''} print:hidden`}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m6 9 6 6 6-6" />
            </svg>
          </span>
          <span className="text-[13px] text-(--muted) sm:text-[14px]">{remote ? home : role.place}</span>
        </span>
      </button>
      <div
        id={panel}
        className={`grid transition-[grid-template-rows] duration-500 ease-[cubic-bezier(0.33,1,0.68,1)] motion-reduce:transition-none ${open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'} print:grid-rows-[1fr]`}
      >
        <div className="overflow-hidden" inert={!open}>
          <ul className="space-y-2 px-4 pt-3 pb-5 pl-[68px] text-[14px] leading-relaxed text-(--body) sm:pl-[72px] print:pt-0">
            {role.points.map((point) => (
              <li key={point.slice(0, 32)} className={DOT}>
                {point}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  )
}

/** The fixed index beside the column on a wide window, marking the section in view. */
function Index() {
  const [active, setActive] = useState(SECTIONS[0].id)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const seen = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (seen[0]) setActive(seen[0].target.id.replace('-section', ''))
      },
      { rootMargin: '0px 0px -60% 0px' },
    )
    SECTIONS.forEach(({ id }) => {
      const section = document.getElementById(`${id}-section`)
      if (section) observer.observe(section)
    })
    return () => observer.disconnect()
  }, [])

  return (
    <nav aria-label="Sections" className="fixed top-[22vh] left-[calc(50%+306px)] hidden flex-col gap-4 lg:flex print:hidden">
      <h2 className="mb-1 text-[10px] font-bold tracking-[0.2em] text-(--muted) uppercase">Index</h2>
      {SECTIONS.map(({ id, label }) => (
        <a
          key={id}
          href={`#${id}`}
          aria-current={active === id ? 'true' : undefined}
          className={`flex items-center gap-3 text-[12.5px] tracking-[0.02em] transition-colors hover:text-(--ink) ${FOCUS} ${active === id ? 'text-(--ink)' : 'pl-6 text-(--muted)'}`}
        >
          {active === id && <span aria-hidden="true" className="h-px w-3 bg-(--muted)" />}
          {label}
        </a>
      ))}
    </nav>
  )
}

/**
 * The résumé as one narrow column of text between dotted rails, after parascodes.is-a.dev: a banner, a small grey
 * portrait beside the name, a few lines on the work, then each job as a row that opens on its points, the skills as
 * chips, and the schooling as cards. Every job's points are word for word what resume.pdf says.
 */
export function ResumePage() {
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('resume-theme')
    setDark(saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches)
  }, [])

  const toggle = () => {
    localStorage.setItem('resume-theme', dark ? 'light' : 'dark')
    setDark(!dark)
  }

  const socials = [...profile.socials, { label: 'Résumé', href: profile.resume.href }]
  const coursework = cv.skills.find((skill) => skill.label === 'Relevant coursework')
  const skills = cv.skills.filter((skill) => skill !== coursework)
  const [college, school] = cv.education

  return (
    <div
      style={dark ? DARK : LIGHT}
      className="min-h-screen overflow-x-hidden bg-(--page) font-['Geist_Variable',system-ui,sans-serif] text-[16px] leading-6 text-(--ink) antialiased transition-colors duration-300 print:bg-white"
    >
      <Index />

      <div className="relative mx-auto max-w-[576px] print:max-w-none">
        <span aria-hidden="true" className={`absolute inset-y-0 -left-px w-px ${DOTS_Y} max-sm:hidden print:hidden`} />
        <span aria-hidden="true" className={`absolute inset-y-0 -right-px w-px ${DOTS_Y} max-sm:hidden print:hidden`} />
        <div
          aria-hidden="true"
          className="h-[160px] bg-[url(/objects/resume/banner.avif)] bg-cover bg-center [mask-composite:intersect] [mask-image:linear-gradient(to_bottom,black_55%,transparent),linear-gradient(to_right,transparent,black_8%,black_92%,transparent)] sm:h-[198px] print:hidden"
        />

        <Rule />
        <header className="relative flex items-center gap-4 px-4 py-3 sm:gap-5 print:px-0">
          <span className="shrink-0 rounded-[8px] border border-(--line) bg-(--page) p-[3px] shadow-[0_1px_2px_rgb(0_0_0/0.08)]">
            <img src="/objects/resume/avatar.avif" alt={cv.name} className="size-[76px] rounded-[5px] object-cover grayscale sm:size-[80px]" />
          </span>
          <div className="flex flex-col justify-center pt-8">
            <h1 className="text-[22px] leading-tight font-bold tracking-tight text-(--ink) sm:text-[24px]">{cv.name}</h1>
            <p className="text-[13px] text-(--muted) sm:text-[14px]">{home}</p>
          </div>
          <button
            type="button"
            onClick={toggle}
            aria-label={dark ? 'Use the light theme' : 'Use the dark theme'}
            className={`absolute top-3 right-4 grid size-8 place-items-center rounded-md text-(--muted) transition-colors hover:bg-(--hover) hover:text-(--ink) ${FOCUS} print:hidden`}
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" className="size-[18px]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {dark ? (
                <>
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
                </>
              ) : (
                <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
              )}
            </svg>
          </button>
        </header>
        <Rule />

        <section className="px-4 pt-4 pb-6">
          <p className="text-[14px] leading-relaxed text-(--body) sm:text-[15px]">
            Full stack developer. I build the software warehouses ship with: automation engines, packing-station apps and shipping labels.
          </p>
          <ul className="mt-4 space-y-1 pl-4 text-[14px] leading-relaxed text-(--body) sm:pl-6 sm:text-[15px]">
            <li className={DOT}>
              Built Cybership's Automation Rules engine from scratch. It runs <strong className="font-semibold text-(--ink)">50,000+ rule executions</strong> a day.
            </li>
            <li className={DOT}>
              Built its Shipping Labels system across 5 carrier APIs, printing <strong className="font-semibold text-(--ink)">10,000+ labels</strong> a day at{' '}
              <strong className="font-semibold text-(--ink)">99.9% uptime</strong>.
            </li>
            <li className={DOT}>
              Currently a <strong className="font-semibold text-(--ink)">Full Stack Developer at Cybership</strong>, working remotely from {home.split(',')[0]}.
            </li>
          </ul>

          <div className="mt-6 flex flex-wrap gap-2 print:hidden">
            <a
              href={profile.resume.href}
              className={`flex items-center gap-1.5 rounded-[4px] bg-(--button) px-3 py-1.5 text-[12px] font-medium tracking-[-0.025em] text-(--button-ink) shadow-[inset_0_1px_0_rgb(255_255_255/0.15),0_1px_2px_rgb(0_0_0/0.2)] transition-opacity hover:opacity-90 ${FOCUS}`}
            >
              {ICONS.download}
              Download the PDF
            </a>
            <a href={`mailto:${profile.email}`} className={`${CHIP} tracking-[-0.025em]`}>
              {ICONS.mail}
              Send an email
            </a>
          </div>

          <h2 className="mt-6 mb-2 text-[14px] text-(--muted)">
            Here are my <span className="font-medium text-(--ink)">socials</span>
          </h2>
          <ul className="flex flex-wrap gap-2">
            {socials.map((social) => (
              <li key={social.label}>
                <a href={social.href} className={CHIP}>
                  {ICONS[social.label]}
                  {social.label}
                </a>
              </li>
            ))}
          </ul>
        </section>

        <section id="experience-section" aria-labelledby="experience">
          <Heading id="experience">Experience</Heading>
          {cv.roles.map((role) => (
            <Role key={role.company} role={role} />
          ))}
        </section>

        <section id="skills-section" aria-labelledby="skills">
          <Heading id="skills">Skills and interests</Heading>
          <div className="flex flex-col gap-5 px-4 pt-6 pb-8">
            {skills.map((skill) => (
              <div key={skill.label}>
                <h3 className={LABEL}>{skill.label}</h3>
                <ul className="mt-2 flex flex-wrap gap-2">
                  {skill.value.split(', ').map((item) => (
                    <li key={item} className="rounded-md border border-(--chip-line) bg-(--chip) px-3 py-1.5 text-[13px] leading-[19.5px] font-medium text-(--body)">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section id="education-section" aria-labelledby="education">
          <Heading id="education">Education</Heading>
          <div className="grid gap-4 px-4 pt-6 pb-10 sm:grid-cols-2">
            <div className="rounded-lg border border-(--line) bg-(--chip)">
              <div className="p-4">
                <h3 className="text-[14px] font-semibold text-(--ink)">{college.school.split(', ')[0]}</h3>
                <p className="mt-1 text-[13px] text-(--body)">{college.course}</p>
                <p className="mt-1 text-[12px] text-(--muted)">
                  {college.grade} · {college.school.split(', ')[1]}
                </p>
              </div>
              {coursework && (
                <div className={`${DOTS_X} bg-top p-4`}>
                  <h4 className={LABEL}>{coursework.label}</h4>
                  <ul className="mt-2 flex flex-col items-start gap-2">
                    {coursework.value.split(', ').map((item) => (
                      <li key={item} className="rounded-md border border-(--chip-line) bg-(--page) px-2.5 py-1 text-[12px] font-medium text-(--body)">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="self-start rounded-lg border border-(--line) bg-(--chip) p-4">
              <h3 className="text-[14px] font-semibold text-(--ink)">{school.school.split(', ')[0]}</h3>
              <p className="mt-1 text-[13px] text-(--body)">{school.course}</p>
              <p className="mt-1 text-[12px] text-(--muted)">
                {school.grade} · {school.school.split(', ')[1]}
              </p>
            </div>
          </div>
        </section>

        <Rule />
        <footer className="flex flex-wrap justify-center gap-2 px-4 py-10 print:hidden">
          <Link to="/" className={STAMP}>
            Back to the site
          </Link>
          <a href={`mailto:${profile.email}`} className={STAMP}>
            {profile.email}
          </a>
        </footer>
        <Rule />
        <div aria-hidden="true" className="h-48 bg-[radial-gradient(var(--line)_1px,transparent_1px)] [background-size:16px_16px] print:hidden" />
      </div>
    </div>
  )
}
