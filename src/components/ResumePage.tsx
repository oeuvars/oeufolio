import '@fontsource-variable/geist'
import '@fontsource-variable/geist-mono'

import { Link, useNavigate } from '@tanstack/react-router'
import { useEffect, useId, useState, type ReactNode } from 'react'

import { cv, pages, profile } from '../content'
import { Activity, useActivity } from './resume/Activity'
import { CommandPalette, PaletteKey } from './resume/CommandPalette'
import { CARD, CHIP, DARK, DOT, DOTS_X, DOTS_Y, FOCUS, LABEL, LIGHT, MONO, PILL, STAMP } from './resume/styles'

const LOGOS: Record<string, string> = {
  'Cybership.io': '/objects/resume/cybership.png',
  'Ekarth Ventures': '/objects/resume/ekarth.png',
  'DataVerse India': '/objects/resume/dataverse.png',
}

const SECTIONS = [
  { id: 'experience', label: 'Experience' },
  { id: 'projects', label: 'Projects' },
  { id: 'activity', label: 'Activity' },
  { id: 'skills', label: 'Skills' },
  { id: 'education', label: 'Education' },
  { id: 'likes', label: 'Likes and music' },
  { id: 'highlights', label: 'Highlights' },
]

/** The systems the résumé's points describe, each as a card. Every figure is one resume.pdf gives. */
const PROJECTS = [
  {
    name: 'Automation Rules',
    company: 'Cybership.io',
    live: true,
    about: 'A rules engine like Shopify Flow, with 50 triggers, 16 condition operators and 7 actions. Its Zod-checked evaluator runs 50,000+ rules a day across orders, inventory and shipping.',
    stack: ['TypeScript', 'Zod'],
  },
  {
    name: 'Cybership Desktop',
    company: 'Cybership.io',
    live: true,
    about: 'The packing-station app that replaced PrintNode. It prints over the OS spooler, raw TCP, USB and HID, reads scales through 64 protocol decoders, and never reprints a job a crash cut short.',
    stack: ['macOS', 'Windows', 'PostgreSQL'],
  },
  {
    name: 'Shipping Labels',
    company: 'Cybership.io',
    live: true,
    about: 'Labels from FedEx, UPS, USPS, DHL and Canada Post through 5 carrier APIs, with Redis-cached rate shopping. It prints 10,000+ labels a day in under 2 seconds each.',
    stack: ['EasyPost', 'Redis', 'pdf-lib'],
  },
  {
    name: 'Altern8',
    company: 'Ekarth Ventures',
    live: false,
    about: 'A real estate lending platform on Next.js and Django. I led its frontend and the team building it, and pitched it to investors in the US, Turkey, the Netherlands and India.',
    stack: ['Next.js', 'Django', 'Docker'],
  },
]

/** The site's other pages, each shown by its own link preview. */
const HIGHLIGHTS = (['basics', 'likes', 'work', 'extras', 'contact'] as const).map((id) => ({ id, ...pages[id] }))

const home = profile.extras.particulars.find((particular) => particular.label === 'Based in')?.value ?? ''
const github = profile.socials.find((social) => social.label === 'GitHub')
const user = github?.href.split('/').pop() ?? ''

/** "March 2025 to now" as "Mar 2025 - Present". */
const period = (text: string) =>
  text
    .split(' to ')
    .map((part) => (part === 'now' ? 'Present' : `${part.slice(0, 3)} ${part.split(' ')[1]}`))
    .join(' - ')

function Icon({ children, fill = false, size = 'size-3.5' }: { children: ReactNode; fill?: boolean; size?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={`${size} shrink-0`}
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
  out: (
    <Icon size="size-3">
      <path d="M7 17 17 7M7 7h10v10" />
    </Icon>
  ),
  back: (
    <Icon size="size-3">
      <path d="m12 19-7-7 7-7M19 12H5" />
    </Icon>
  ),
}

/** A rule run the whole width of the window, through the column's rails. */
const Rule = () => <div aria-hidden="true" className={`relative left-1/2 h-px w-screen -translate-x-1/2 ${DOTS_X} print:hidden`} />

/** A section's name, set between two rules, with an aside on the right if it has one. */
function Heading({ id, aside, children }: { id: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <>
      <Rule />
      <div className="flex items-baseline justify-between gap-3 px-4 py-2">
        <h2 id={id} className="scroll-mt-6 text-[18px] leading-[27px] font-bold tracking-tight whitespace-nowrap text-(--ink)">
          {children}
        </h2>
        {aside && <p className="text-right text-[12px] text-(--muted)">{aside}</p>}
      </div>
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
    // The last sections never reach the line the observer watches, so the end of the page marks the last one.
    const onScroll = () => {
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) setActive(SECTIONS[SECTIONS.length - 1].id)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      observer.disconnect()
      window.removeEventListener('scroll', onScroll)
    }
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
 * The résumé as one narrow column between dotted rails, after parascodes.is-a.dev: a banner, a small grey portrait
 * beside the name, a few lines on the work, then each job as a row that opens on its points, the systems it built as
 * cards, a year of GitHub activity, the skills as chips, the schooling as cards, the likes from the desk, and the
 * site's other pages. ⌘K opens a menu of all of it. Every job's points are word for word what resume.pdf says.
 */
export function ResumePage() {
  const navigate = useNavigate()
  const [dark, setDark] = useState(false)
  const year = useActivity(user)

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
  const { likes, playlist } = profile.extras

  const commands = [
    ...SECTIONS.map(({ id, label }) => ({
      group: 'Sections',
      label,
      run: () => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
    })),
    { group: 'Links', label: 'Download the PDF', hint: 'resume.pdf', run: () => window.open(profile.resume.href, '_blank') },
    { group: 'Links', label: 'Send an email', hint: profile.email, run: () => (window.location.href = `mailto:${profile.email}`) },
    ...profile.socials.map((social) => ({ group: 'Links', label: social.label, hint: social.href.replace('https://', ''), run: () => window.open(social.href, '_blank') })),
    { group: 'Links', label: 'Back to the site', run: () => navigate({ to: '/' }) },
    { group: 'Settings', label: dark ? 'Use the light theme' : 'Use the dark theme', run: toggle },
  ]

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
          <div className="absolute top-3 right-4 flex items-center gap-2 print:hidden">
            <CommandPalette commands={commands} trigger={(open) => <PaletteKey onOpen={open} />} />
            <button
              type="button"
              onClick={toggle}
              aria-label={dark ? 'Use the light theme' : 'Use the dark theme'}
              className={`grid size-8 place-items-center rounded-md text-(--muted) transition-colors hover:bg-(--hover) hover:text-(--ink) ${FOCUS}`}
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
          </div>
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

        <section id="projects-section" aria-labelledby="projects">
          <Heading id="projects">Projects</Heading>
          <div className="grid gap-x-10 gap-y-8 px-8 pt-6 pb-8 sm:grid-cols-2 print:px-0">
            {PROJECTS.map((project) => {
              const role = cv.roles.find((r) => r.company === project.company)
              return (
                <article key={project.name} className="flex flex-col">
                  <div className="grid aspect-[3/1] place-items-center sm:aspect-[236/168] rounded-xl border border-(--line) bg-[linear-gradient(to_bottom,var(--chip),var(--hover))] shadow-[0_1px_2px_rgb(0_0_0/0.05)] print:hidden">
                    <span className="grid size-14 place-items-center rounded-xl border border-(--line) bg-white shadow-[0_2px_6px_rgb(0_0_0/0.08)]">
                      <img src={LOGOS[project.company]} alt="" className="size-11 rounded-lg object-contain" />
                    </span>
                  </div>
                  <div className="mt-4 flex items-center justify-between gap-2 px-0.5">
                    <h3 className="text-[15px] leading-tight font-bold text-(--ink)">{project.name}</h3>
                    <span className={PILL}>
                      <span className={`size-1.5 rounded-full ${project.live ? 'bg-emerald-500' : 'bg-(--faint)'}`} />
                      {project.live ? 'Live' : project.company}
                    </span>
                  </div>
                  <p className="mt-2 px-0.5 text-[13px] leading-[1.6] text-(--muted)">{project.about}</p>
                  <div className="mt-auto flex items-center justify-between gap-3 px-0.5 pt-3">
                    <span className={`${MONO} min-w-0 truncate text-[10px] tracking-wide text-(--faint) uppercase`}>{project.stack.join(' · ')}</span>
                    {role && (
                      <a href={role.href} className={`flex shrink-0 items-center gap-1 text-[12px] font-medium text-(--body) hover:text-(--ink) ${FOCUS}`}>
                        {project.live ? 'Cybership' : 'Ekarth'}
                        {ICONS.out}
                      </a>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
        </section>

        <section id="activity-section" aria-labelledby="activity" className="print:hidden">
          <Heading id="activity" aside={year && year !== 'failed' ? `${year.total} contributions in the last year` : undefined}>
            GitHub Activity
          </Heading>
          <Activity year={year} user={user} />
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
          <div className="grid gap-4 px-4 pt-6 pb-8 sm:grid-cols-2">
            <div className={CARD}>
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
            <div className={`${CARD} self-start p-4`}>
              <h3 className="text-[14px] font-semibold text-(--ink)">{school.school.split(', ')[0]}</h3>
              <p className="mt-1 text-[13px] text-(--body)">{school.course}</p>
              <p className="mt-1 text-[12px] text-(--muted)">
                {school.grade} · {school.school.split(', ')[1]}
              </p>
            </div>
          </div>
        </section>

        <section id="likes-section" aria-labelledby="likes" className="print:hidden">
          <Heading id="likes">Likes and music</Heading>
          <div className="px-4 pt-6 pb-8">
            <div className={CARD}>
              <div className="flex items-baseline justify-between gap-3 px-4 py-3">
                <h3 className="text-[14px] font-bold text-(--ink)">
                  Likes <span className="ml-1 text-[12px] font-normal text-(--muted)">what the desk holds</span>
                </h3>
                <span className={`${MONO} text-[10px] text-(--faint)`}>{Object.keys(likes).length} things</span>
              </div>
              <ul className={`${DOTS_X} grid grid-cols-2 gap-3 bg-top p-4 sm:grid-cols-4`}>
                {Object.values(likes).map((like) => (
                  <li key={like.subject} className="flex flex-col rounded-md border border-(--line) bg-(--page) p-3">
                    <span className="text-[12px] font-semibold text-(--ink)">{like.subject}</span>
                    <span className={`${MONO} mt-1 text-[10px] text-(--faint)`}>{like.title}</span>
                    <span className="mt-2 text-[12px] leading-snug text-(--muted)">{like.note}</span>
                  </li>
                ))}
              </ul>
              <div className={`${DOTS_X} bg-top px-4 py-4`}>
                <h3 className="text-[14px] font-bold text-(--ink)">
                  Music <span className="ml-1 text-[12px] font-normal text-(--muted)">one playlist, on the record on my desk</span>
                </h3>
                <a href={playlist.href} className={`${CHIP} mt-3 w-fit`}>
                  {playlist.title}
                  {ICONS.out}
                </a>
              </div>
              <p className={`${DOTS_X} ${MONO} bg-top px-4 py-4 text-[10px] tracking-wider text-(--faint) uppercase`}>
                On repeat <span className="ml-1 text-(--muted)">{playlist.title}</span>
              </p>
            </div>
          </div>
        </section>

        <section id="highlights-section" aria-labelledby="highlights" className="print:hidden">
          <Heading id="highlights">Highlights</Heading>
          <ul className="flex snap-x snap-mandatory gap-4 overflow-x-auto px-4 pt-6 pb-8 [mask-image:linear-gradient(to_right,transparent,black_16px,black_calc(100%-16px),transparent)] [scrollbar-width:none]">
            {HIGHLIGHTS.map((page) => (
              <li key={page.id} className="w-[300px] shrink-0 snap-center">
                <Link to={page.path} className={`group block overflow-hidden rounded-lg border border-(--line) bg-(--chip) ${FOCUS}`}>
                  <img src={page.preview.src} alt="" loading="lazy" className="aspect-[1200/630] w-full object-cover transition-transform duration-500 group-hover:scale-[1.02] motion-reduce:transition-none" />
                  <span className="block p-3">
                    <span className="flex items-center justify-between">
                      <span className={`${MONO} rounded-[4px] bg-(--hover) px-1.5 py-0.5 text-[10px] font-semibold tracking-wider text-(--muted) uppercase`}>{page.path === '/' ? 'Basics' : page.path.slice(1)}</span>
                      <span className="text-(--faint) group-hover:text-(--ink)">{ICONS.out}</span>
                    </span>
                    <span className="mt-2 line-clamp-2 block text-[13px] leading-snug font-semibold text-(--ink)">{page.preview.alt}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <Rule />
        <footer className="px-4 pt-12 pb-10 text-center print:hidden">
          <figure>
            <blockquote className="text-[16px] leading-relaxed text-(--muted) italic">
              <p>
                "A ship in harbor is safe,
                <br />
                but that is not what ships are built for."
              </p>
            </blockquote>
            <figcaption className={`${MONO} mt-5 flex items-center justify-center gap-3 text-[10px] tracking-[0.2em] text-(--faint) uppercase`}>
              <span aria-hidden="true" className="h-px w-4 bg-(--line)" />
              John A. Shedd
              <span aria-hidden="true" className="h-px w-4 bg-(--line)" />
            </figcaption>
          </figure>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            <Link to="/" className={STAMP}>
              {ICONS.back}
              Back to the site
            </Link>
            <a href={`mailto:${profile.email}`} className={STAMP}>
              {ICONS.mail}
              {profile.email}
            </a>
          </div>
        </footer>
        <Rule />
        <div aria-hidden="true" className="h-48 bg-[radial-gradient(var(--line)_1px,transparent_1px)] [background-size:16px_16px] print:hidden" />
      </div>
    </div>
  )
}
