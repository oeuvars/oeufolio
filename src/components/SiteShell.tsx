import { Link, useRouterState } from '@tanstack/react-router'
import { MotionConfig } from 'motion/react'
import type { CSSProperties } from 'react'

import { profile } from '../content'
import { CopyEmail } from './CopyEmail'
import { Reveal } from './Reveal'

type Tone = {
  paper: string
  ink: string
}

const spineTone: Tone = { paper: '#8c8b76', ink: '#34331c' }
const contactTone: Tone = { paper: '#272521', ink: '#d9d2bc' }
const sheetTones: Tone[] = [
  { paper: '#ece4cc', ink: '#2f2e1d' },
  { paper: '#bcbdc2', ink: '#24242a' },
  { paper: '#7d8798', ink: '#14181f' },
  { paper: '#a98a60', ink: '#2a1d0e' },
]

const code = (position: number) => `CODE_${String(position).padStart(3, '0')}`

function toneStyle(tone: Tone, extra: Record<string, string> = {}): CSSProperties {
  return { '--paper': tone.paper, '--ink': tone.ink, ...extra } as CSSProperties
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

  return (
    <MotionConfig reducedMotion="user">
      <main
        className="grain fixed inset-0 flex overflow-hidden bg-[#1d1c1a]"
        style={{ '--strip': 'clamp(3rem, 6.5vw, 6rem)', '--tab-w': 'clamp(1.7rem, 2.6vw, 2.4rem)' } as CSSProperties}
      >
        <aside
          className="sheet z-0 flex !min-w-[clamp(4.6rem,13vh,8rem)] flex-none flex-col justify-between py-[3vh] pr-[2.4rem] pl-[0.8rem]"
          style={toneStyle(spineTone)}
        >
          <Link
            to="/"
            aria-label={profile.handle}
            className="display vertical self-start whitespace-nowrap text-[min(6.2vh,5vw)] no-underline"
          >
            {profile.handle}_01-0{profile.nav.length}
          </Link>
          <div className="flex items-end justify-between gap-[0.4rem]">
            <p className="label vertical hidden whitespace-nowrap opacity-80 md:block">{profile.colophon}</p>
            <p className="label whitespace-nowrap max-md:hidden">FILE_01//</p>
          </div>
        </aside>

        {profile.nav.map((item, i) => {
          const open = i === index
          const tab = (
            <span className="tab-text vertical">
              <span className="label">{code(i + 1)} //</span>
              <span className="label">{item.label}</span>
            </span>
          )

          return (
            <section
              key={item.to}
              className={open ? 'sheet is-open' : 'sheet'}
              style={toneStyle(sheetTones[i], { zIndex: String(i + 1), '--tab-top': `${2 + i * 2.6}rem` })}
            >
              <Link
                to={item.to}
                activeOptions={{ exact: true }}
                aria-label={item.label}
                aria-current={open ? 'page' : undefined}
                className="tab"
              >
                {tab}
              </Link>

              {open ? (
                <div className="scroll-quiet flex h-full flex-col overflow-y-auto px-[clamp(1.1rem,3vw,3.2rem)] py-[3vh] text-[clamp(14px,0.35vw+1.1vh,19px)] leading-[1.5]">
                  <Reveal>
                    <div className="row label flex justify-between pb-[0.7em]">
                      <span>FILE_0{i + 1}//</span>
                      <span>{profile.handle}</span>
                    </div>
                  </Reveal>
                  <div key={pathname} className="grid flex-1 content-center py-[4vh]">
                    {children}
                  </div>
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
                </div>
              ) : (
                <Link
                  to={item.to}
                  tabIndex={-1}
                  aria-hidden
                  className="absolute inset-0 flex items-end justify-center pb-[3vh] no-underline"
                >
                  <span className="display vertical text-[clamp(1.5rem,5vh,3.4rem)] opacity-90">{item.label}</span>
                </Link>
              )}
            </section>
          )
        })}

        <aside
          className="sheet z-10 hidden !min-w-[clamp(4.5rem,8vw,7.5rem)] flex-none flex-col items-center justify-between pt-[calc(var(--tab-top)+9rem)] pb-[3vh] md:flex"
          style={toneStyle(contactTone, { '--tab-top': `${2 + profile.nav.length * 2.6}rem` })}
        >
          <div className="tab">
            <span className="tab-text vertical">
              <span className="label">{code(profile.nav.length + 1)} //</span>
              <span className="label">Contact</span>
            </span>
          </div>
          <CopyEmail email={profile.email} className="vertical" />
          <div className="flex flex-col items-center gap-[1.4em]">
            <ul className="vertical flex gap-[1.2em]">
              {profile.socials.map((social) => (
                <li key={social.label}>
                  <a href={social.href} target="_blank" rel="noreferrer" className="label link">
                    {social.label}
                  </a>
                </li>
              ))}
            </ul>
            <p className="label vertical whitespace-nowrap opacity-70">&copy; 2026 {profile.handle}</p>
          </div>
        </aside>
      </main>
    </MotionConfig>
  )
}
