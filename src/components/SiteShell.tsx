import { Link, useRouterState } from '@tanstack/react-router'
import { MotionConfig, motion, useReducedMotion } from 'motion/react'
import type { CSSProperties } from 'react'

import { profile } from '../content'
import { Art } from './Art'
import { CopyEmail } from './CopyEmail'
import { useStackMetrics } from './useStackMetrics'

type Tone = {
  band: string
  bandInk: string
  panel: string
  panelInk: string
}

const spineTone: Tone = { band: '#b78f86', bandInk: '#3a1512', panel: '#b78f86', panelInk: '#3a1512' }
const contactTone: Tone = { band: '#8a8b78', bandInk: '#20241a', panel: '#10150f', panelInk: '#efe6cb' }
const pageTones: Tone[] = [
  { band: '#6f2f2a', bandInk: '#ecd9c6', panel: '#e8cdc4', panelInk: '#3a1512' },
  { band: '#7a8597', bandInk: '#121820', panel: '#bcbdc2', panelInk: '#24242a' },
  { band: '#b8946a', bandInk: '#2a1a0a', panel: '#2a1b10', panelInk: '#f0e2c6' },
  { band: '#d9d4c2', bandInk: '#1e1d19', panel: '#141311', panelInk: '#e6dfca' },
]
const tabTops = [5, 9, 4, 6.5, 8.5, 4.5]
const tabHeights = [11, 10, 10, 10, 10, 11.5]

const slide = { type: 'spring', stiffness: 150, damping: 21, mass: 1 } as const
const instant = { duration: 0 } as const

function stripStyle(tone: Tone, slot: number, z: number, extra: Record<string, string | number> = {}): CSSProperties {
  return {
    '--band': tone.band,
    '--band-ink': tone.bandInk,
    '--panel': tone.panel,
    '--panel-ink': tone.panelInk,
    '--paper': tone.panel,
    '--ink': tone.panelInk,
    '--tab-top': `${tabTops[slot]}rem`,
    '--tab-h': `${tabHeights[slot]}rem`,
    zIndex: z,
    ...extra,
  } as CSSProperties
}

type TabProps = {
  code?: number
  label: string
  to?: '/' | '/likes' | '/work' | '/extras'
  current?: boolean
}

function Tab({ code, label, to, current }: TabProps) {
  const text = (
    <span className="tab-text vertical">
      {code !== undefined && <span className="mono">CODE_{String(code).padStart(3, '0')} //</span>}
      <span className="label">{label}</span>
    </span>
  )

  if (!to) return <div className="tab">{text}</div>

  return (
    <Link
      to={to}
      activeOptions={{ exact: true }}
      aria-label={label}
      aria-current={current ? 'page' : undefined}
      className="tab"
    >
      {text}
    </Link>
  )
}

type SiteShellProps = {
  children: React.ReactNode
}

export function SiteShell({ children }: SiteShellProps) {
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  const index = Math.max(
    0,
    profile.nav.findIndex((item) => item.to === pathname),
  )
  const count = profile.nav.length
  const stack = count + 3
  const { metrics, ready } = useStackMetrics()
  const reduced = useReducedMotion()
  const transition = ready && !reduced ? slide : instant

  const { overlap, band, protrude, strip, spine, contact, end, mobile } = metrics
  const fixed = mobile ? 0 : spine + contact + end
  const gaps = (mobile ? count : count + 3) - 1
  const openWidth = metrics.width - fixed - (count - 1) * strip + gaps * overlap
  const panelWidth = openWidth - band
  const artWidth = strip - band - overlap

  const lefts: number[] = []
  let cursor = mobile ? 0 : spine - overlap
  for (let i = 0; i < count; i++) {
    lefts.push(cursor)
    cursor += (i === index ? openWidth : strip) - overlap
  }
  const contactLeft = cursor

  return (
    <MotionConfig reducedMotion="user">
      <main
        className="grain fixed inset-0 overflow-hidden bg-[#1f1e1b]"
        style={{ '--band-w': `${band}px`, '--protrude': `${protrude}px` } as CSSProperties}
      >
        {!mobile && (
          <aside className="strip" style={stripStyle(spineTone, 0, stack + 1, { left: 0, width: spine })}>
            <div className="absolute inset-y-0 left-0 flex flex-col py-[3vh]" style={{ right: band }}>
              <Link
                to="/"
                aria-label={profile.handle}
                className="display vertical ml-[1.1rem] self-start whitespace-nowrap text-[min(6.4vh,5vw)] no-underline"
              >
                {profile.handle}_01-0{count}
              </Link>
              <div className="mt-auto ml-[1.1rem] flex items-end gap-[0.9rem]">
                <p className="mono vertical rotate-180 leading-[1.7] font-bold whitespace-nowrap">
                  Product Studies:
                  <br />
                  Type · Image · Craft
                </p>
              </div>
              <p className="mono mt-[1.4rem] ml-[1.1rem] font-bold">FILE_01//</p>
            </div>
            <Tab label="Home" to="/" current={false} />
          </aside>
        )}

        {profile.nav.map((item, i) => {
          const open = i === index

          return (
            <motion.section
              key={item.to}
              className="strip"
              initial={false}
              animate={{ left: lefts[i], width: open ? openWidth : strip }}
              transition={transition}
              style={stripStyle(pageTones[i], i + 1, stack - i)}
            >
              <div className="panel scroll-quiet overflow-x-hidden overflow-y-auto">
                <motion.div
                  aria-hidden
                  className="absolute inset-y-0"
                  style={{ left: overlap, width: artWidth }}
                  initial={false}
                  animate={{ opacity: open ? 0 : 1 }}
                  transition={{ duration: 0.35 }}
                >
                  <Art index={i} />
                </motion.div>

                {open ? (
                  <motion.div
                    className="@container relative flex min-h-full flex-col pr-[clamp(1rem,2.6vw,3rem)] py-[2.4vh] text-[clamp(14px,0.35vw+1.1vh,19px)] leading-[1.5]"
                    style={{ width: panelWidth, minWidth: 0, paddingLeft: overlap + protrude + 16, '--clear': `${overlap + protrude}px` } as CSSProperties}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.45, delay: 0.3, ease: [0.215, 0.61, 0.355, 1] }}
                  >
                    <div className="grid flex-1 content-center py-[4vh]">{children}</div>
                    <footer className="label flex flex-col gap-[0.6em] border-t border-ink/30 pt-[0.9em] md:hidden">
                      <CopyEmail email={profile.email} />
                      <ul className="flex gap-[1.2em]">
                        {profile.socials.map((social) => (
                          <li key={social.label}>
                            <a href={social.href} target="_blank" rel="noreferrer" className="link">
                              {social.label}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </footer>
                  </motion.div>
                ) : (
                  <Link to={item.to} tabIndex={-1} aria-hidden className="absolute inset-0 z-10" />
                )}
              </div>
              <Tab code={i + 1} label={item.label} to={item.to} current={open} />
            </motion.section>
          )
        })}

        {!mobile && (
          <>
            <aside
              className="strip"
              style={stripStyle(contactTone, count + 1, 2, { left: contactLeft, width: contact })}
            >
              <div className="panel flex flex-col items-center justify-between py-[3vh]">
                <img
                  src="/photos/street.jpg"
                  alt=""
                  className="absolute inset-0 size-full object-cover opacity-80 [filter:hue-rotate(75deg)_saturate(0.55)_brightness(0.6)_contrast(1.1)]"
                />
                <span
                  aria-hidden
                  className="absolute inset-y-[0.6rem] left-[1.4rem] w-[calc(100%-2.2rem)] border-2 border-r-0 border-[#d8b24a] shadow-[0_0_8px_rgb(216_178_74/0.45)] [clip-path:polygon(0_0,calc(100%-0.5rem)_0,100%_1.4rem,100%_100%,0_100%)]"
                />
                <CopyEmail email={profile.email} className="vertical relative mt-[4vh]" />
                <div className="relative flex flex-col items-center gap-[1.4em]">
                  <ul className="vertical flex gap-[1.2em]">
                    {profile.socials.map((social) => (
                      <li key={social.label}>
                        <a href={social.href} target="_blank" rel="noreferrer" className="label link">
                          {social.label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              <Tab code={count + 1} label="Contact" />
            </aside>

            <div aria-hidden className="absolute inset-y-0 right-0 z-0 bg-[#1f1e1b]" style={{ width: end }} />
          </>
        )}
      </main>
    </MotionConfig>
  )
}
