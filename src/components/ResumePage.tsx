import '@fontsource-variable/geist'
import '@fontsource-variable/geist-mono'

import { Link, useNavigate } from '@tanstack/react-router'
import { useEffect, useId, useRef, useState, type CSSProperties, type ReactNode } from 'react'

import { cv, pages, profile } from '../content'
import { Activity, useActivity } from './resume/Activity'
import { CommandPalette, PaletteKey } from './resume/CommandPalette'
import { Guestbook, signHref, useGuestbook } from './resume/Guestbook'
import { TechIcon } from './resume/TechIcon'
import { CARD, CHIP, DASH_X, DASH_Y, FOCUS, KNOT, LABEL, MONO, RING, RULE, STAMP } from './resume/styles'

const LOGOS: Record<string, string> = {
  'Cybership.io': '/objects/resume/cybership.png',
  'Ekarth Ventures': '/objects/resume/ekarth.png',
  'DataVerse India': '/objects/resume/dataverse.png',
}

/** The systems the résumé's points describe, each as a card. Every figure is one resume.pdf gives. */
const PROJECTS = [
  {
    name: 'Automation Rules',
    company: 'Cybership.io',
    status: 'Live',
    about: 'A rules engine like Shopify Flow, with 50 triggers, 16 condition operators and 7 actions. Its Zod-checked evaluator runs 50,000+ rules a day across orders, inventory and shipping.',
    stack: ['TypeScript', 'Zod'],
  },
  {
    name: 'Cybership Desktop',
    company: 'Cybership.io',
    status: 'Live',
    about: 'The packing-station app that replaced PrintNode. It prints over the OS spooler, raw TCP, USB and HID, reads scales through 64 protocol decoders, and never reprints a job a crash cut short.',
    stack: ['macOS', 'Windows', 'PostgreSQL'],
  },
  {
    name: 'Shipping Labels',
    company: 'Cybership.io',
    status: 'Live',
    about: 'Labels from FedEx, UPS, USPS, DHL and Canada Post through 5 carrier APIs, with Redis-cached rate shopping. It prints 10,000+ labels a day in under 2 seconds each.',
    stack: ['EasyPost', 'Redis', 'pdf-lib'],
  },
  {
    name: 'Altern8',
    company: 'Ekarth Ventures',
    status: 'Shipped',
    about: 'A real estate lending platform on Next.js and Django. I led its frontend and the team building it, and pitched it to investors in the US, Turkey, the Netherlands and India.',
    stack: ['Next.js', 'Django', 'Docker'],
  },
]

const HIGHLIGHTS = (['basics', 'likes', 'work', 'extras', 'contact'] as const).map((id) => ({ id, ...pages[id] }))

const home = profile.extras.particulars.find((particular) => particular.label === 'Based in')?.value ?? ''
const user = profile.socials.find((social) => social.label === 'GitHub')?.href.split('/').pop() ?? ''
const repo = `${user}/${user}`

const GRADIENT_TOP: CSSProperties = { background: 'linear-gradient(rgb(255, 255, 255) 0%, rgba(255, 255, 255, 0) 100%)' }
const GRADIENT_FOOT: CSSProperties = { background: 'radial-gradient(65.62% 65.62% at 50% 100%, rgb(0, 0, 0) 0%, rgba(0, 0, 0, 0) 100%)' }
const GRADIENT_SHEEN: CSSProperties = { background: 'linear-gradient(99deg, rgba(255, 255, 255, 0) 27.7%, rgba(255, 255, 255, 0.12) 60.19%, rgba(255, 255, 255, 0) 86.06%)' }
const GRADIENT_EDGE: CSSProperties = {
  background: 'linear-gradient(rgb(255, 255, 255) 0%, rgb(153, 153, 153) 55%, rgb(255, 255, 255) 80%, rgb(153, 153, 153) 95%)',
  WebkitMask: 'linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)',
  WebkitMaskComposite: 'xor',
  maskComposite: 'exclude',
}

/** "March 2025 to now" as "Mar 2025 - Present". */
const period = (text: string) =>
  text
    .split(' to ')
    .map((part) => (part === 'now' ? 'Present' : `${part.slice(0, 3)} ${part.split(' ')[1]}`))
    .join(' - ')

function Icon({ children, className = 'size-3.5', fill = false }: { children: ReactNode; className?: string; fill?: boolean }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={`${className} shrink-0`}
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

const PATHS: Record<string, ReactNode> = {
  GitHub: (
    <>
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </>
  ),
  Instagram: (
    <>
      <rect width="20" height="20" x="2" y="2" rx="5" />
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37zM17.5 6.5h.01" />
    </>
  ),
  Résumé: <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7ZM14 2v4a2 2 0 0 0 2 2h4M16 13H8M16 17H8M10 9H8" />,
  mail: (
    <>
      <rect width="20" height="16" x="2" y="4" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </>
  ),
  download: <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />,
  out: <path d="M7 17 17 7M7 7h10v10" />,
  pin: <path d="M12 17v5M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z" />,
  message: <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />,
  back: <path d="m12 19-7-7 7-7M19 12H5" />,
  briefcase: <path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16M2 8a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z" />,
  code: <path d="m16 18 6-6-6-6M8 6l-6 6 6 6" />,
  activity: <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2" />,
  book: <path d="M12 7v14M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z" />,
  cap: <path d="M21.42 10.92a1 1 0 0 0-.02-1.84L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.83l8.57 3.91a2 2 0 0 0 1.66 0zM22 10v6M6 12.5V16a6 3 0 0 0 12 0v-3.5" />,
  music: <path d="M9 18V5l12-2v13M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM21 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" />,
  sparkles: <path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0l1.58 6.14a2 2 0 0 0 1.44 1.44l6.14 1.58a.5.5 0 0 1 0 .96l-6.14 1.58a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0zM20 3v4M22 5h-4" />,
  sun: <path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />,
  moon: <path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401" />,
  laptop: <path d="M18 5a2 2 0 0 1 2 2v8.526a2 2 0 0 0 .212.897l1.068 2.127a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45l1.068-2.127A2 2 0 0 0 4 15.526V7a2 2 0 0 1 2-2zM20.054 15.987H3.946" />,
}

const glyph = (name: string, className?: string) =>
  name === 'X' ? (
    <Icon className={className} fill>
      <path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.4l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.6l5.24 6.93Zm-1.29 19.5h2.04L6.49 3.24H4.3Z" />
    </Icon>
  ) : (
    <Icon className={className}>{PATHS[name]}</Icon>
  )

const SECTIONS = [
  { id: 'experience', label: 'Experience', icon: 'briefcase', key: 'E' },
  { id: 'projects', label: 'Projects', icon: 'code', key: 'P' },
  { id: 'activity', label: 'GitHub Activity', icon: 'activity', key: 'A' },
  { id: 'skills', label: 'Skills', icon: 'book', key: 'S' },
  { id: 'education', label: 'Education', icon: 'cap', key: 'G' },
  { id: 'likes', label: 'Likes & Music', icon: 'music', key: 'L' },
  { id: 'highlights', label: 'Highlights', icon: 'sparkles', key: 'H' },
  { id: 'guestbook', label: 'Guestbook', icon: 'message', key: 'B' },
]

/** A rule run the whole width of the window, with its two knots where it crosses the column's rails. */
function Crossing({ edge }: { edge: 'top' | 'bottom' }) {
  const top = edge === 'top'
  return (
    <>
      <div aria-hidden="true" className={`${RULE} ${top ? 'top-0 border-t' : 'bottom-0 border-b'} right-[-100vw] left-[-100vw]`} style={DASH_X} />
      <div aria-hidden="true" className={`${KNOT} ${top ? 'top-0 -translate-y-1/2' : 'bottom-0 translate-y-1/2'} -left-4 -translate-x-1/2`} />
      <div aria-hidden="true" className={`${KNOT} ${top ? 'top-0 -translate-y-1/2' : 'bottom-0 translate-y-1/2'} -right-4 translate-x-1/2`} />
    </>
  )
}

/** A section: rules above and below its name, its content, and a rule closing it. */
function Section({ id, title, aside, after, children, className = '' }: { id: string; title: string; aside?: ReactNode; after?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className={`relative z-10 mt-6 flex scroll-mt-24 flex-col ${className}`}>
      <Crossing edge="top" />
      <div className="relative py-2">
        <div className="flex items-center justify-between gap-3">
          <h2 id={`${id}-title`} className="text-[18px] font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
            {title}
          </h2>
          {aside}
        </div>
        <Crossing edge="bottom" />
      </div>
      {children}
      <Crossing edge="bottom" />
      {after}
    </section>
  )
}

/** A button's face as the reference draws one: a fill, a highlight, a shadow and a sheen stacked under the label. */
function Face({ dark = false }: { dark?: boolean }) {
  return dark ? (
    <span className="absolute inset-0 overflow-hidden rounded-[4px] border border-black/10 bg-[#18181b] transition-colors duration-200 group-hover:bg-[#27272a] group-active:duration-[50ms] dark:border-white/10 dark:bg-white dark:group-hover:bg-neutral-100">
      <span className="absolute inset-0 opacity-[0.12] transition duration-200 group-active:opacity-0 group-active:duration-[50ms]" style={GRADIENT_TOP} />
      <span className="absolute inset-0 opacity-[0.32] transition duration-200 group-active:duration-[50ms]" style={GRADIENT_FOOT} />
      <span className="absolute inset-0 rounded-[4px] p-px opacity-[0.24]" style={GRADIENT_EDGE} />
    </span>
  ) : (
    <span className="absolute inset-0 overflow-hidden rounded-[4px] border border-black/5 bg-white/90 transition-colors duration-200 group-hover:border-black/10 group-active:duration-[50ms] dark:border-white/5 dark:bg-[#0c0c0e] dark:group-hover:border-white/10 dark:group-hover:bg-[#121214]">
      <span className="absolute inset-0 rounded-[4px] bg-black/[0.02] transition duration-200 group-hover:bg-transparent group-active:bg-black/[0.04] group-active:duration-[50ms] dark:bg-transparent dark:group-hover:bg-white/[0.02] dark:group-active:bg-white/[0.04]" />
      <span className="absolute inset-0 opacity-[0.16] transition duration-200 group-active:opacity-0 group-active:duration-[50ms] dark:opacity-[0.04]" style={GRADIENT_TOP} />
      <span className="absolute inset-0 opacity-[0.04] transition duration-200 group-active:duration-[50ms] dark:opacity-[0.1]" style={GRADIENT_FOOT} />
      <span className="absolute inset-0 opacity-[0.4] transition duration-200 group-active:opacity-0 group-active:duration-[50ms] dark:opacity-[0.04]" style={GRADIENT_SHEEN} />
    </span>
  )
}

const FACE_TEXT = 'rounded-[4px] px-3 py-1.5 text-center text-[12px] font-medium tracking-tight [backdrop-filter:blur(6px)]'

/** The reference's light button: a link on the light face, its label brightening on hover. */
function Button({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      className={`group relative block ${FACE_TEXT} text-neutral-900 transition-[transform] duration-200 active:scale-[0.99] active:duration-[50ms] dark:text-neutral-300 ${FOCUS}`}
    >
      <Face />
      <span className="relative">
        <span className="flex items-center gap-1.5 opacity-70 transition-opacity duration-300 group-hover:opacity-100">{children}</span>
      </span>
    </a>
  )
}

/**
 * The reference's lid button: a dark face that flips up on its bottom edge when hovered or focused, showing the real
 * link under it. The flip itself is in styles.css (.resume-flip).
 */
function FlipButton({ href, label, children, back }: { href: string; label: string; children: ReactNode; back: ReactNode }) {
  const front = (
    <span className="relative">
      <span className="flex items-center gap-1.5 whitespace-nowrap">{children}</span>
    </span>
  )
  return (
    <div className="resume-flip">
      <div aria-hidden="true" className={`group pointer-events-none relative block opacity-0 ${FACE_TEXT} text-neutral-50 dark:text-neutral-950`}>
        <Face dark />
        {front}
      </div>
      <div className="resume-flip-link">
        <a
          href={href}
          aria-label={label}
          className={`inline-flex h-full w-full items-center justify-center gap-1.5 rounded-[4px] border border-white/10 bg-zinc-900 px-3 py-1.5 text-[12px] font-semibold tracking-wide whitespace-nowrap text-white shadow-sm transition-colors hover:bg-black dark:border-black/10 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100 ${FOCUS}`}
        >
          {back}
        </a>
      </div>
      <div aria-hidden="true" className="resume-flip-cover">
        <div className="resume-flip-inside">
          <div className="flex items-center gap-1.5 text-[12px] font-semibold whitespace-nowrap text-white">{back}</div>
        </div>
        <div className="resume-flip-spine" />
        <div className="resume-flip-outside">
          <div className={`group pointer-events-none relative flex h-full w-full items-center justify-center whitespace-nowrap ${FACE_TEXT} text-neutral-50 dark:text-neutral-950`}>
            <Face dark />
            {front}
          </div>
        </div>
      </div>
      <div aria-hidden="true" className="resume-flip-shadow" />
    </div>
  )
}

/** The reference's View All button, opening the site's page with more of a section. */
function ViewAll({ to, overlap = false }: { to: string; overlap?: boolean }) {
  const link = (
    <Link to={to} className={`group relative block ${FOCUS}`}>
      <div className="pointer-events-none absolute -inset-[5px] rounded-[11px] border border-black/5 transition-colors duration-300 group-hover:border-black/10 dark:border-white/5 dark:group-hover:border-white/10" />
      <div className="relative flex items-center gap-1.5 rounded-[6px] border border-black/5 bg-zinc-50 px-4 py-2 text-[13px] font-medium text-zinc-600 shadow-sm shadow-black/20 transition-all duration-300 hover:bg-zinc-100 hover:text-zinc-900 dark:border-white/5 dark:bg-[#09090b] dark:text-zinc-400 dark:shadow-lg dark:shadow-black/80 dark:hover:bg-[#121214] dark:hover:text-zinc-100">
        View All
        {glyph('out', 'size-3.5 text-zinc-500 transition-colors group-hover:text-zinc-900 dark:group-hover:text-zinc-300')}
      </div>
    </Link>
  )
  return overlap ? (
    <div className="relative z-20 -mt-[19px] flex justify-center pb-0 print:hidden">{link}</div>
  ) : (
    <div className="relative -mx-4 flex cursor-pointer justify-center rounded-b-lg px-4 py-4 transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-900/20 print:hidden">{link}</div>
  )
}

/** One job: its logo, employer, title, dates and place, opening on its points. */
function Role({ role }: { role: (typeof cv.roles)[number] }) {
  const [open, setOpen] = useState(false)
  const panel = useId()
  const remote = role.place === 'Remote'

  return (
    <div className="group/role relative">
      <div aria-hidden="true" className={`${RULE} right-[-16px] bottom-0 left-[-16px] z-10 border-b`} style={DASH_X} />
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panel}
        onClick={() => setOpen(!open)}
        className={`relative z-20 -mx-4 flex w-[calc(100%+2rem)] cursor-pointer flex-col items-start gap-2.5 rounded-lg px-4 py-3.5 text-left transition-colors hover:bg-zinc-50 sm:gap-3 sm:py-4 2xl:flex-row 2xl:items-center 2xl:justify-between dark:hover:bg-zinc-900/20 ${FOCUS}`}
      >
        <span className="flex min-w-0 flex-1 items-start gap-3 sm:gap-4">
          <span className="size-10 shrink-0 rounded-[10px] border border-black/10 bg-zinc-50 p-[2px] shadow-sm shadow-black/15 dark:border-zinc-800 dark:bg-[#111111] dark:shadow-md dark:shadow-black/50">
            <span className="relative flex h-full w-full items-center justify-center overflow-hidden rounded-[7px] border border-black/5 bg-white dark:border-black/20">
              <img src={LOGOS[role.company]} alt={role.company} className="h-full w-full object-cover" />
            </span>
          </span>
          <span className="flex min-w-0 flex-col gap-0.5 pr-2 sm:pr-4">
            <span className="flex flex-wrap items-center gap-2">
              <span className="text-[14px] leading-tight font-bold text-zinc-900 sm:text-[17px] dark:text-zinc-100">{role.company}</span>
              {remote && (
                <span className="self-center rounded-[4px] border border-zinc-300/50 bg-zinc-200/50 px-1.5 py-[1px] text-[11px] font-medium whitespace-nowrap text-zinc-600 dark:border-zinc-700/50 dark:bg-zinc-800/50 dark:text-zinc-400">
                  Remote
                </span>
              )}
            </span>
            <span className="truncate text-[14px] text-zinc-600 sm:text-[15px] dark:text-zinc-400">{role.title}</span>
          </span>
        </span>
        <span className="flex shrink-0 flex-col items-start gap-0.5 pr-5 pl-[52px] text-left sm:pl-[56px] 2xl:mt-0 2xl:items-end 2xl:pl-0 2xl:text-right">
          <span className="relative flex items-center text-[13px] font-medium text-zinc-900 sm:text-[14px] dark:text-zinc-100">
            <span>{period(role.period)}</span>
            <svg
              aria-hidden="true"
              viewBox="0 0 24 24"
              className={`absolute top-1/2 -right-5 -mt-[1.5px] size-3.5 -translate-y-1/2 text-zinc-500 transition-transform duration-300 ${open ? 'rotate-180' : ''} print:hidden`}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m6 9 6 6 6-6" />
            </svg>
          </span>
          <span className="text-[13px] text-zinc-500 sm:text-[14px] dark:text-zinc-400">{remote ? home : role.place}</span>
        </span>
      </button>
      <div
        id={panel}
        className={`-mx-4 grid transition-[grid-template-rows] duration-500 ease-[cubic-bezier(0.33,1,0.68,1)] ${open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'} print:grid-rows-[1fr]`}
      >
        <div className="overflow-hidden" inert={!open}>
          <div
            className={`pr-8 pl-6 text-[14px] text-zinc-600 transition-all duration-500 ease-[cubic-bezier(0.33,1,0.68,1)] dark:text-zinc-400 ${open ? 'translate-y-0 pt-2 pb-1 opacity-100' : '-translate-y-2 pt-0 pb-0 opacity-0'} print:translate-y-0 print:opacity-100`}
          >
            {role.about && <p className="mb-2 text-[13px] text-zinc-500 dark:text-zinc-500">{role.about}</p>}
            <ul className="mb-4 space-y-2 text-[13px] leading-relaxed">
              {role.points.map((point) => (
                <li key={point.slice(0, 32)} className="flex items-start gap-1.5">
                  <span aria-hidden="true" className="mt-[2px] text-[14px] leading-none text-zinc-400 dark:text-zinc-500">
                    •
                  </span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

/** One system the résumé describes, as the reference's project card: a framed panel, its name and status, a line on
 * what it does, and the tools it was built with. */
function Project({ project }: { project: (typeof PROJECTS)[number] }) {
  const role = cv.roles.find((r) => r.company === project.company)
  return (
    <a href={role?.href} className={`group flex cursor-pointer flex-col ${FOCUS}`}>
      <div className="relative flex aspect-[1.25] w-full flex-col overflow-hidden rounded-xl border border-black/5 bg-zinc-50/80 p-3.5 pb-0 shadow-sm transition-[border-color,box-shadow] duration-200 hover:border-black/10 hover:shadow-md sm:aspect-[1.4] sm:p-4 sm:pb-0 dark:border-white/5 dark:bg-[#09090b]/80 dark:hover:border-white/10 print:hidden">
        <div className="z-10 flex min-h-[24px] items-center justify-end">
          <div className="flex size-6 items-center justify-center rounded-[6px] border border-zinc-200/80 bg-transparent text-zinc-400 dark:border-zinc-800/80 dark:text-zinc-500">{glyph('pin')}</div>
        </div>
        <div className="absolute bottom-0 left-1/2 z-20 flex h-[66%] w-[85%] origin-bottom -translate-x-1/2 items-center justify-center rounded-t-[10px] border border-b-0 border-black/5 bg-white shadow-[0_-8px_30px_rgba(0,0,0,0.06)] sm:h-[74%] dark:border-white/[0.15] dark:bg-[#0a0a0a] dark:shadow-[0_-8px_30px_rgba(0,0,0,0.5)]">
          <span className="size-14 rounded-[12px] border border-black/10 bg-zinc-50 p-[2px] shadow-sm shadow-black/15 transition-transform duration-300 group-hover:scale-105 dark:border-zinc-800 dark:bg-[#111111]">
            <img src={LOGOS[project.company]} alt="" className="h-full w-full rounded-[9px] border border-black/5 bg-white object-cover" />
          </span>
        </div>
      </div>
      <div className="mt-4 flex flex-col px-0.5">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center sm:gap-0">
          <h3 className="text-[15px] leading-tight font-bold text-zinc-900 dark:text-zinc-100">{project.name}</h3>
          <div className="flex w-fit shrink-0 items-center gap-1.5 rounded-full border border-zinc-200/50 bg-white px-2 py-0.5 dark:border-zinc-800/50 dark:bg-zinc-900/50">
            <div className={`size-1.5 rounded-full ${project.status === 'Live' ? 'bg-emerald-500' : 'bg-zinc-400 dark:bg-zinc-500'}`} />
            <span className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">{project.status}</span>
          </div>
        </div>
        <p className="mt-2 pr-2 text-[13px] leading-relaxed text-zinc-500 sm:mt-1.5 dark:text-zinc-400">{project.about}</p>
        <div className="mt-3 flex items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {project.stack.map((item) => (
              <div key={item} className="relative" title={item}>
                <TechIcon name={item} className="size-4 text-zinc-400 transition-colors hover:text-zinc-800 md:size-3.5 dark:text-zinc-500 dark:hover:text-zinc-200" />
                <span className="sr-only">{item}</span>
              </div>
            ))}
          </div>
          <div className="flex shrink-0 cursor-pointer items-center gap-1 text-[11px] font-medium text-zinc-500 transition-colors group-hover:text-zinc-800 sm:text-[12px] dark:group-hover:text-zinc-200">
            View Project
            {glyph('out', 'size-3')}
          </div>
        </div>
      </div>
    </a>
  )
}

/** The fixed index beside the column on a wide window, marking the section in view. */
function Index() {
  const [active, setActive] = useState(SECTIONS[0].id)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const seen = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (seen[0]) setActive(seen[0].target.id)
      },
      { rootMargin: '0px 0px -60% 0px' },
    )
    SECTIONS.forEach(({ id }) => {
      const section = document.getElementById(id)
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
    <div className="pointer-events-none fixed inset-0 z-50 hidden lg:block print:hidden">
      <nav aria-label="Sections" className="pointer-events-auto absolute top-[22vh] left-[calc(69%+32px)] mt-2 flex flex-col gap-4">
        <h3 className="mb-1 text-[10px] font-bold tracking-[0.2em] text-zinc-500 uppercase dark:text-zinc-500">Index</h3>
        {SECTIONS.map(({ id, label }) => (
          <a
            key={id}
            href={`#${id}`}
            aria-current={active === id ? 'true' : undefined}
            className={`flex items-center gap-3 text-[12px] font-medium tracking-[0.05em] transition-all duration-300 ease-out ${FOCUS} ${active === id ? 'text-zinc-800 dark:text-zinc-200' : 'text-zinc-500 hover:text-zinc-700 dark:text-zinc-500 dark:hover:text-zinc-300'}`}
          >
            <span className={`h-[1px] transition-all duration-300 ease-out ${active === id ? 'w-3 bg-zinc-400 dark:bg-zinc-600' : 'w-0 bg-transparent'}`} />
            {label}
          </a>
        ))}
      </nav>
    </div>
  )
}

/** The dot grid closing the page, which brightens in a circle around the pointer. */
function Field() {
  const glow = useRef<HTMLDivElement>(null)
  const dots: CSSProperties = { backgroundImage: 'radial-gradient(circle, currentColor 1px, transparent 1px)', backgroundSize: '16px 16px', backgroundPosition: 'center' }

  return (
    <div
      className="relative -mx-4 mt-4 h-[300px] w-[calc(100%+32px)] grow print:hidden"
      onMouseMove={(event) => {
        const box = event.currentTarget.getBoundingClientRect()
        const mask = `radial-gradient(250px circle at ${event.clientX - box.left}px ${event.clientY - box.top}px, black, transparent)`
        if (glow.current) Object.assign(glow.current.style, { maskImage: mask, webkitMaskImage: mask, opacity: '1' })
      }}
      onMouseLeave={() => glow.current && (glow.current.style.opacity = '0')}
    >
      <div aria-hidden="true" className={`${RULE} top-0 right-[-100vw] left-[-100vw] z-10 border-t`} style={DASH_X} />
      <div aria-hidden="true" className={`${KNOT} top-0 left-0 -translate-x-1/2 -translate-y-1/2`} />
      <div aria-hidden="true" className={`${KNOT} top-0 right-0 translate-x-1/2 -translate-y-1/2`} />
      <div aria-hidden="true" className="absolute inset-0 h-full w-full overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 h-full w-full text-zinc-400 opacity-20 transition-opacity duration-500 dark:text-zinc-500 dark:opacity-[0.1]"
          style={{ ...dots, maskImage: 'linear-gradient(to bottom, black 0%, transparent 100%)', WebkitMaskImage: 'linear-gradient(to bottom, black 0%, transparent 100%)' }}
        />
        <div ref={glow} className="pointer-events-none absolute inset-0 h-full w-full text-zinc-500 opacity-0 transition-opacity duration-700 ease-in-out dark:text-zinc-400" style={dots} />
      </div>
    </div>
  )
}

type Theme = 'light' | 'dark' | 'system'

/**
 * The résumé, copied from parascodes.is-a.dev down to its classes: one column between dotted rails, a banner over a
 * band holding the portrait and name, a few lines on the work, then each job as a row that opens on its points, the
 * systems it built as cards, a year of GitHub activity, the skills, the schooling, the likes from the desk, the site's
 * other pages running past, and a guestbook kept on GitHub. ⌘K opens a menu of all of it. Every job's points are word
 * for word what resume.pdf says.
 */
export function ResumePage() {
  const navigate = useNavigate()
  const [theme, setTheme] = useState<Theme>('system')
  const [system, setSystem] = useState(false)
  const year = useActivity(user)
  const notes = useGuestbook(repo)
  const dark = theme === 'dark' || (theme === 'system' && system)

  useEffect(() => {
    const saved = localStorage.getItem('resume-theme')
    if (saved === 'light' || saved === 'dark' || saved === 'system') setTheme(saved)
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    setSystem(media.matches)
    const onChange = () => setSystem(media.matches)
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  const choose = (next: Theme) => {
    localStorage.setItem('resume-theme', next)
    setTheme(next)
  }

  const socials = [...profile.socials, { label: 'Résumé', href: profile.resume.href }]
  const coursework = cv.skills.find((skill) => skill.label === 'Relevant coursework')
  const skills = cv.skills.filter((skill) => skill !== coursework)
  const [college, school] = cv.education
  const { likes, playlist } = profile.extras
  const playlistId = playlist.href.split('/').pop()
  const open = (href: string) => window.open(href, '_blank', 'noopener')

  const commands = [
    ...SECTIONS.map(({ id, label, icon, key }) => ({
      group: 'Sections',
      label,
      key,
      icon: glyph(icon, 'size-4'),
      run: () => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
    })),
    { group: 'Links', label: 'Download the PDF', key: 'R', icon: glyph('download', 'size-4'), run: () => open(profile.resume.href) },
    { group: 'Links', label: 'Send an email', key: 'M', icon: glyph('mail', 'size-4'), run: () => (window.location.href = `mailto:${profile.email}`) },
    ...profile.socials.map((social) => ({ group: 'Profiles', label: social.label, icon: glyph(social.label, 'size-4'), run: () => open(social.href) })),
    { group: 'Links', label: 'Back to the site', icon: glyph('back', 'size-4'), run: () => navigate({ to: '/' }) },
    { group: 'Theme', label: 'Light', key: 'T', icon: glyph('sun', 'size-4'), run: () => choose('light') },
    { group: 'Theme', label: 'Dark', key: 'D', icon: glyph('moon', 'size-4'), run: () => choose('dark') },
    { group: 'Theme', label: 'System', key: 'U', icon: glyph('laptop', 'size-4'), run: () => choose('system') },
  ]

  const highlight = (page: (typeof HIGHLIGHTS)[number], copy: boolean) => (
    <Link key={`${page.id}${copy ? '-copy' : ''}`} to={page.path} tabIndex={copy ? -1 : undefined} aria-hidden={copy || undefined} className={`block ${FOCUS}`}>
      <div className="group relative w-[300px] flex-shrink-0">
        <div className="pointer-events-none absolute -inset-[4px] rounded-[10px] border border-black/5 transition-colors duration-300 group-hover:border-black/10 dark:border-white/5 dark:group-hover:border-white/10" />
        <div className="relative flex flex-col overflow-hidden rounded-[6px] border border-black/5 bg-zinc-50 shadow-sm shadow-black/5 transition-all duration-300 group-hover:bg-zinc-100/80 dark:border-white/5 dark:bg-[#09090b] dark:shadow-lg dark:shadow-black/80 dark:group-hover:bg-[#121214]">
          <div className="relative h-[200px] w-full overflow-hidden bg-zinc-100 dark:bg-[#0a0a0a]">
            <img
              src={page.preview.src}
              alt={copy ? '' : page.preview.alt}
              loading="lazy"
              className="absolute inset-0 h-full w-full object-cover object-top grayscale transition-[filter,transform] duration-500 ease-out group-hover:grayscale-0 motion-safe:group-hover:scale-[1.025]"
            />
          </div>
          <div className="flex h-[86px] flex-col gap-1.5 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="inline-flex items-center rounded-[4px] border border-black/5 bg-black/5 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-zinc-600 uppercase dark:border-white/5 dark:bg-white/5 dark:text-zinc-400">
                {page.path === '/' ? 'Basics' : page.path.slice(1)}
              </span>
              <div className="flex shrink-0 items-center gap-2">
                {glyph('out', 'size-3.5 text-zinc-400 transition-colors group-hover:text-zinc-900 dark:text-zinc-500 dark:group-hover:text-zinc-100')}
              </div>
            </div>
            <p className="line-clamp-2 text-[13px] leading-snug font-medium text-zinc-800 transition-colors group-hover:text-zinc-900 dark:text-zinc-200 dark:group-hover:text-white">{page.preview.alt}</p>
          </div>
        </div>
      </div>
    </Link>
  )

  return (
    <div
      className={`relative min-h-screen w-full overflow-x-hidden bg-white font-['Geist_Variable',system-ui,sans-serif] text-[16px] leading-normal text-black antialiased transition-colors duration-300 dark:bg-black dark:text-zinc-50 ${dark ? 'dark [color-scheme:dark]' : ''}`}
    >
      <Index />

      <div aria-hidden="true" className="pointer-events-none absolute top-0 bottom-0 left-[30%] hidden w-0 border-r border-black/30 md:block dark:border-white/[0.15] print:hidden" style={DASH_Y} />
      <div aria-hidden="true" className="pointer-events-none absolute top-0 right-[30%] bottom-0 hidden w-0 border-r border-black/30 md:block dark:border-white/[0.15] print:hidden" style={DASH_Y} />
      <div aria-hidden="true" className={`${RULE} top-[22vh] right-0 left-0 border-b print:hidden`} style={DASH_X} />
      <div aria-hidden="true" className={`${RULE} top-[calc(22vh+112px)] right-0 left-0 border-b print:hidden`} style={DASH_X} />
      {['left', 'right'].flatMap((side) =>
        ['22vh', 'calc(22vh + 112px)'].map((top) => (
          <div
            key={`${side}${top}`}
            aria-hidden="true"
            className={`${KNOT} z-10 hidden md:block print:hidden`}
            style={{ top, [side]: '30%', transform: `translate(${side === 'left' ? '-50%' : '50%'}, -50%)` }}
          />
        )),
      )}

      <div className="absolute top-0 right-0 left-0 -z-0 h-[22vh] overflow-hidden bg-white shadow-[0_4px_12px_rgba(2,6,23,0.04)] md:right-[30%] md:left-[30%] dark:bg-black dark:shadow-[0_4px_12px_rgba(2,6,23,0.10)] print:hidden">
        <img src="/objects/resume/banner.avif" alt="" className="absolute inset-0 h-full w-full object-cover object-center" />
        <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 bottom-0 z-[5] h-10 bg-linear-to-t from-white/90 to-transparent dark:from-black/50" />
        <div aria-hidden="true" className="pointer-events-none absolute top-0 bottom-0 left-0 z-20 w-8 bg-linear-to-r from-white/90 to-transparent dark:from-black/40" />
        <div aria-hidden="true" className="pointer-events-none absolute top-0 right-0 bottom-0 z-20 w-8 bg-linear-to-l from-white/90 to-transparent dark:from-black/40" />
      </div>

      <header className="absolute top-[22vh] right-0 left-0 z-50 flex h-[112px] items-center px-4 md:right-[30%] md:left-[30%] print:static print:h-auto">
        <div className="flex w-full items-center justify-between">
          <div className="flex items-center gap-4 sm:gap-5">
            <div className="relative shrink-0 rounded-[6px] border-[1.5px] border-black/30 p-[3px] sm:rounded-[8px] dark:border-white/[0.15]">
              <div className="relative size-16 overflow-hidden rounded-[3px] bg-zinc-100 sm:size-20 sm:rounded-[5px] dark:bg-zinc-900">
                <img
                  src="/objects/resume/avatar.avif"
                  alt="Profile"
                  className="h-full w-full origin-center translate-y-1 scale-[1.1] object-cover opacity-90 contrast-100 grayscale mix-blend-multiply dark:mix-blend-normal"
                />
              </div>
            </div>
            <div className="flex flex-col justify-center pt-8">
              <h1 className="mb-0.5 text-[20px] leading-none font-bold tracking-tight text-zinc-800 [text-shadow:-1.5px_0_0_rgba(0,200,255,0.3),1.5px_0_0_rgba(255,80,0,0.3)] sm:text-[24px] dark:text-zinc-100 dark:[text-shadow:-1.5px_0_0_rgba(0,200,255,0.6),1.5px_0_0_rgba(255,80,0,0.6)]">
                {cv.name}
              </h1>
              <p className="text-[13px] text-zinc-500 sm:text-[14px] dark:text-zinc-400">{home}</p>
            </div>
          </div>
          <div className="flex h-20 items-start justify-end gap-2 py-1 sm:h-24 sm:gap-3 print:hidden">
            <CommandPalette commands={commands} trigger={(show) => <PaletteKey onOpen={show} />} />
            <button
              type="button"
              onClick={() => choose(dark ? 'light' : 'dark')}
              aria-label="Toggle theme"
              aria-pressed={dark}
              className="relative z-50 flex size-[18px] cursor-pointer items-center justify-center text-zinc-500 transition-all duration-300 hover:text-zinc-900 active:scale-95 dark:text-zinc-400 hover:dark:text-zinc-300"
            >
              {glyph(dark ? 'sun' : 'moon', 'size-[18px]')}
            </button>
          </div>
        </div>
      </header>

      <main className="relative z-10 mr-0 ml-0 flex min-h-screen flex-col px-4 pt-[calc(22vh+112px)] pb-0 md:mr-[30%] md:ml-[30%] print:mx-0 print:pt-4">
        <p className="mt-4 text-[14px] leading-relaxed text-zinc-600 sm:text-[15px] dark:text-zinc-300">
          Full stack developer. I build the software warehouses ship with: automation engines, packing-station apps and shipping labels.
        </p>
        <ul className="mt-4 pl-4 text-[14px] leading-relaxed text-zinc-600 sm:text-[15px] dark:text-zinc-300">
          {[
            <>
              Built Cybership's Automation Rules engine from scratch. It runs <span className="font-semibold text-zinc-900 dark:text-white">50,000+ rule executions</span> a day.
            </>,
            <>
              Built its Shipping Labels system across 5 carrier APIs, printing <span className="font-semibold text-zinc-900 dark:text-white">10,000+ labels</span> a day at{' '}
              <span className="font-semibold text-zinc-900 dark:text-white">99.9% uptime</span>.
            </>,
            <>
              Currently a <span className="font-semibold text-zinc-900 dark:text-white">Full Stack Developer at Cybership</span>, working remotely from {home.split(',')[0]}.
            </>,
          ].map((line, i) => (
            <li key={i} className="flex gap-1.5">
              <span aria-hidden="true">•</span>
              <span>{line}</span>
            </li>
          ))}
        </ul>

        <div className="mt-4 flex flex-wrap items-center gap-2 print:hidden">
          <FlipButton
            href={profile.resume.href}
            label="Download the PDF"
            back={
              <>
                {glyph('Résumé')}
                <span>resume.pdf</span>
              </>
            }
          >
            {glyph('download')}
            <span className="whitespace-nowrap">Download the PDF</span>
          </FlipButton>
          <Button href={`mailto:${profile.email}`}>
            {glyph('mail')}
            Send an email
          </Button>
        </div>

        <div className="mt-6 scroll-mt-24">
          <h2 className="mb-2 text-[14px] text-zinc-500">
            Here are my <span className="font-medium text-zinc-800 dark:text-zinc-200">socials</span>
          </h2>
          <div className="flex flex-wrap gap-1.5">
            {socials.map((social) => (
              <span key={social.label} className="inline-block">
                <Button href={social.href}>
                  {glyph(social.label)}
                  {social.label}
                </Button>
              </span>
            ))}
          </div>
        </div>

        <Section id="experience" title="Experiences">
          <div className="mt-0 block">
            {cv.roles.map((role) => (
              <Role key={role.company} role={role} />
            ))}
          </div>
          <ViewAll to="/work" />
        </Section>

        <Section id="projects" title="Projects" after={<ViewAll to="/work" overlap />}>
          <div className="relative px-4 pt-6 pb-12">
            <div aria-hidden="true" className="pointer-events-none absolute top-0 bottom-6 left-1/2 hidden w-0 -translate-x-1/2 border-r border-black/30 md:block dark:border-white/[0.15]" style={DASH_Y} />
            <div className="relative z-10 flex w-full flex-col">
              {[PROJECTS.slice(0, 2), PROJECTS.slice(2)].map((row, r) => (
                <div key={r} className="relative">
                  {r > 0 && (
                    <div aria-hidden="true" className="relative h-0">
                      <div className={`${RULE} top-0 right-[-100vw] left-[-100vw] border-t`} style={DASH_X} />
                      <div className={`${KNOT} top-0 -left-8 -translate-x-1/2 -translate-y-1/2`} />
                      <div className={`${KNOT} top-0 -right-8 translate-x-1/2 -translate-y-1/2`} />
                      <div className={`${KNOT} top-0 left-1/2 hidden -translate-x-1/2 -translate-y-1/2 md:block`} />
                    </div>
                  )}
                  <div className={`grid grid-cols-1 gap-x-10 gap-y-10 md:grid-cols-2 md:gap-y-0 ${r > 0 ? 'pt-6' : 'pb-10 md:pb-6'}`}>
                    {row.map((project) => (
                      <Project key={project.name} project={project} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Section>

        <Section
          id="activity"
          title="GitHub Activity"
          className="print:hidden"
          aside={
            <p className="text-right text-[11px] text-zinc-500 dark:text-zinc-400">
              {year === null ? 'Loading GitHub contribution activity' : year === 'failed' ? '' : `${year.total} GitHub activities in the last year`}
            </p>
          }
        >
          <Activity year={year} user={user} />
        </Section>

        <Section id="skills" title="Skills & Technologies">
          <div className="relative flex flex-col gap-5 pt-6 pb-6">
            {skills.map((skill) => (
              <div key={skill.label}>
                <p className={LABEL}>{skill.label}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {skill.value.split(', ').map((item) => (
                    <div
                      key={item}
                      className="flex cursor-default items-center gap-2 rounded-[6px] border border-black/30 bg-zinc-50 px-3 py-1.5 transition-colors duration-200 hover:bg-zinc-100 dark:border-white/[0.15] dark:bg-[#0a0a0a] dark:hover:bg-[#121214]"
                    >
                      <TechIcon name={item} />
                      <span className="text-[13px] font-medium text-zinc-600 dark:text-zinc-400">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section id="education" title="Education">
          <div className="relative grid gap-5 pt-6 pb-6 md:grid-cols-2">
            <div className="group relative">
              <div className={RING} />
              <div className={`${CARD} h-full`}>
                <div className="px-4 pt-3 pb-3">
                  <h3 className="text-[14px] font-bold tracking-tight text-zinc-900 dark:text-zinc-100">{college.school.split(', ')[0]}</h3>
                  <p className="mt-1 text-[13px] text-zinc-600 dark:text-zinc-400">{college.course}</p>
                  <p className="mt-0.5 text-[12px] text-zinc-500 dark:text-zinc-500">
                    {college.grade} · {college.school.split(', ')[1]}, India
                  </p>
                </div>
                <div className="h-px bg-black/30 dark:bg-white/[0.15]" style={DASH_X} />
                {coursework && (
                  <div className="px-4 py-3.5">
                    <p className="text-[10px] font-medium text-zinc-400 uppercase dark:text-zinc-600">{coursework.label}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {coursework.value.split(', ').map((item) => (
                        <span key={item} className={CHIP}>
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="group relative">
              <div className={RING} />
              <div className={`${CARD} h-full`}>
                <div className="px-4 pt-3 pb-3">
                  <h3 className="text-[14px] font-bold tracking-tight text-zinc-900 dark:text-zinc-100">School</h3>
                </div>
                <div className="h-px bg-black/30 dark:bg-white/[0.15]" style={DASH_X} />
                <div className="px-4 py-3">
                  <p className="text-[13px] font-medium text-zinc-900 dark:text-zinc-100">{school.school.split(', ')[0]}</p>
                  <p className="mt-0.5 text-[12px] text-zinc-500 dark:text-zinc-500">
                    {school.course} · {school.grade} · {school.school.split(', ')[1]}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Section>

        <Section id="likes" title="Likes & Music" className="print:hidden">
          <div className="relative flex flex-col gap-5 pt-6 pb-2">
            <div className="group relative">
              <div className={RING} />
              <div className={CARD}>
                <header className="flex flex-wrap items-center gap-x-2 gap-y-1 px-4 pt-3 pb-2.5">
                  <h3 className="text-[14px] font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Likes</h3>
                  <span className="text-[12px] text-zinc-400 dark:text-zinc-600">what the desk holds</span>
                  <span className={`${MONO} ml-auto text-[11px] text-zinc-400 tabular-nums dark:text-zinc-600`}>{Object.keys(likes).length} things · 1 playlist</span>
                </header>
                <div className="h-px bg-black/30 dark:bg-white/[0.15]" style={DASH_X} />
                <div className="grid grid-cols-2 gap-3 p-4 sm:grid-cols-4">
                  {Object.values(likes).map((like) => (
                    <div key={like.subject} className="group/card relative">
                      <div className="relative flex aspect-[2/3] w-full flex-col justify-between overflow-hidden rounded-[5px] border border-black/5 bg-zinc-100 p-2.5 dark:border-white/5 dark:bg-[#0a0a0a]">
                        <span className={`${MONO} text-[10px] text-zinc-400 dark:text-zinc-600`}>{like.title}</span>
                        <span className="text-[12px] leading-snug text-zinc-500 italic dark:text-zinc-400">{like.note}</span>
                      </div>
                      <p className="mt-1.5 truncate text-[11px] font-medium text-zinc-600 dark:text-zinc-400">{like.subject}</p>
                    </div>
                  ))}
                </div>
                <div className="h-px bg-black/30 dark:bg-white/[0.15]" style={DASH_X} />
                <div className="flex flex-col gap-3 px-4 py-3.5">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <h3 className="text-[14px] font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Music</h3>
                    <span className="text-[12px] text-zinc-400 dark:text-zinc-600">the playlist on the record on my desk</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <a href={playlist.href} className={`${CHIP} hover:text-zinc-900 dark:hover:text-zinc-200`}>
                      {playlist.title}
                    </a>
                  </div>
                </div>
                <div className="h-px bg-black/30 dark:bg-white/[0.15]" style={DASH_X} />
                <div className="px-4 py-3.5">
                  <div className="flex items-baseline gap-2 pb-2.5">
                    <p className={LABEL}>On repeat</p>
                    <span className={`${MONO} text-[10px] text-zinc-400 dark:text-zinc-600`}>{playlist.title}</span>
                  </div>
                  <div className="overflow-hidden rounded-[10px]">
                    <iframe
                      title={`${playlist.title} on Spotify`}
                      src={`https://open.spotify.com/embed/playlist/${playlistId}?utm_source=generator`}
                      height="152"
                      loading="lazy"
                      allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                      className="block w-full"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
          <ViewAll to="/extras" />
        </Section>

        <Section id="highlights" title="Highlights" className="print:hidden">
          <div className="relative mt-4 overflow-hidden py-2">
            <div aria-hidden="true" className="pointer-events-none absolute top-0 bottom-0 left-0 z-10 w-5 bg-linear-to-r from-white/70 to-transparent dark:from-black/70" />
            <div aria-hidden="true" className="pointer-events-none absolute top-0 right-0 bottom-0 z-10 w-5 bg-linear-to-l from-white/70 to-transparent dark:from-black/70" />
            <div className="flex w-max animate-[highlights-marquee_28s_linear_infinite] items-start gap-4 px-1 hover:[animation-play-state:paused] motion-reduce:animate-none">
              {HIGHLIGHTS.map((page) => highlight(page, false))}
              {HIGHLIGHTS.map((page) => highlight(page, true))}
            </div>
          </div>
          <div className="mt-2">
            <ViewAll to="/" />
          </div>
        </Section>

        <section id="guestbook" aria-labelledby="guestbook-title" className="relative mt-6 flex scroll-mt-24 flex-col print:hidden">
          <Crossing edge="top" />
          <div className="relative py-2">
            <div className="flex items-baseline justify-between gap-3">
              <h2 id="guestbook-title" className="text-[18px] font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
                Guestbook
              </h2>
              <span className={`${MONO} shrink-0 text-[10px] tracking-[0.14em] text-zinc-400 uppercase dark:text-zinc-600`}>via GitHub</span>
            </div>
            <Crossing edge="bottom" />
          </div>
          <Guestbook repo={repo} notes={notes} />
        </section>

        <div className="relative mt-2 flex flex-col items-center justify-center py-6 print:hidden">
          <figure className="flex w-full max-w-[480px] flex-col items-center">
            <blockquote className="mb-6 text-center text-[16px] leading-relaxed font-medium text-zinc-500 italic dark:text-zinc-400">
              "A ship in harbor is safe,
              <br className="hidden md:block" /> but that is not what ships are built for."
            </blockquote>
            <figcaption className="flex items-center gap-3 text-[10px] font-medium tracking-[0.2em] text-zinc-400 uppercase dark:text-zinc-600">
              <div className="h-[1px] w-4 bg-zinc-200 dark:bg-zinc-800" />
              John A. Shedd
              <div className="h-[1px] w-4 bg-zinc-200 dark:bg-zinc-800" />
            </figcaption>
          </figure>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-2 pb-6 print:hidden">
          <a href={signHref(repo)} className={STAMP}>
            {glyph('message', 'size-3')}
            Sign the guestbook
          </a>
          <Link to="/" className={STAMP}>
            {glyph('back', 'size-3')}
            Back to the site
          </Link>
        </div>

        <Field />
      </main>
    </div>
  )
}
