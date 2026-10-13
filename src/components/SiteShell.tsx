import { Link, useRouterState } from '@tanstack/react-router'
import { MotionConfig } from 'motion/react'
import type { CSSProperties } from 'react'

import { profile } from '../content'
import { Art } from './Art'
import { CopyEmail } from './CopyEmail'
import { Reveal } from './Reveal'

type Tone = {
  paper: string
  ink: string
}

const spineTone: Tone = { paper: '#8c8b76', ink: '#34331c' }
const contactTone: Tone = { paper: '#7c7d6a', ink: '#20241a' }
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
  const count = profile.nav.length
  const stack = count + 2

  return (
    <MotionConfig reducedMotion="user">
      <main className="grain fixed inset-0 flex overflow-hidden bg-[#1d1c1a] [--overlap:0.9rem] [--strip:3.1rem] [--tab-w:2.4rem] md:[--strip:clamp(6rem,10.5vw,10rem)] md:[--tab-w:3rem]">
        <aside
          className="sheet !m-0 hidden !min-w-[clamp(5.4rem,16vh,9rem)] flex-none flex-col justify-between !p-0 py-[3vh] md:flex"
          style={toneStyle(spineTone, { zIndex: String(stack) })}
        >
          <Link
            to="/"
            aria-label={profile.handle}
            className="display vertical ml-[1.1rem] self-start whitespace-nowrap text-[min(6.4vh,5vw)] no-underline"
          >
            {profile.handle}_01-0{count}
          </Link>
          <div className="mx-[1.1rem] flex items-end justify-between gap-[0.5rem]">
            <p className="label vertical whitespace-nowrap opacity-80">{profile.colophon}</p>
            <p className="label whitespace-nowrap">FILE_01//</p>
          </div>
        </aside>

        {profile.nav.map((item, i) => {
          const open = i === index

          return (
            <section
              key={item.to}
              className={open ? 'sheet is-open' : 'sheet'}
              style={toneStyle(sheetTones[i], {
                zIndex: String(stack - 1 - i),
                '--tab-h': `${7.2 + i * 1.6}rem`,
              })}
            >
              <Link
                to={item.to}
                activeOptions={{ exact: true }}
                aria-label={item.label}
                aria-current={open ? 'page' : undefined}
                className="tab"
              >
                <span className="tab-text vertical">
                  <span className="label">{code(i + 1)} //</span>
                  <span className="label">{item.label}</span>
                </span>
              </Link>

              {open ? (
                <div className="card card-page @container scroll-quiet overflow-y-auto">
                  <div className="flex min-h-full flex-col px-[clamp(1rem,2.6vw,3rem)] py-[2.4vh] text-[clamp(14px,0.35vw+1.1vh,19px)] leading-[1.5]">
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
                </div>
              ) : (
                <Link to={item.to} tabIndex={-1} aria-hidden className="card max-md:hidden">
                  <Art index={i} />
                  <span
                    className={`display vertical absolute bottom-[3%] left-1/2 -translate-x-1/2 text-[clamp(1.5rem,5vh,3.4rem)] ${i === count - 1 ? 'text-[#efe6cb]' : ''}`}
                  >
                    {item.label}
                  </span>
                </Link>
              )}
            </section>
          )
        })}

        <aside
          className="sheet z-0 hidden !min-w-[clamp(6rem,10vw,9rem)] flex-none md:flex"
          style={toneStyle(contactTone, { '--tab-h': `${7.2 + count * 1.6}rem` })}
        >
          <div className="tab">
            <span className="tab-text vertical">
              <span className="label">{code(count + 1)} //</span>
              <span className="label">Contact</span>
            </span>
          </div>
          <div className="card flex flex-col items-center justify-between bg-[#141311] py-[3vh] text-[#efe6cb]">
            <img src="/photos/street.jpg" alt="" className="absolute inset-0 size-full object-cover opacity-55" />
            <span
              aria-hidden
              className="absolute inset-[0.5rem] border-2 border-[#d8b24a] [clip-path:polygon(0_0.9rem,0.9rem_0,calc(100%-0.9rem)_0,100%_0.9rem,100%_calc(100%-0.9rem),calc(100%-0.9rem)_100%,0.9rem_100%,0_calc(100%-0.9rem))]"
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
              <p className="label vertical whitespace-nowrap opacity-70">&copy; 2026 {profile.handle}</p>
            </div>
          </div>
        </aside>
      </main>
    </MotionConfig>
  )
}
