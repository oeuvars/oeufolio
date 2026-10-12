import { Link, useRouterState } from '@tanstack/react-router'
import { MotionConfig } from 'motion/react'

import { profile } from '../content'
import { CopyEmail } from './CopyEmail'
import { Reveal } from './Reveal'
import { Dial } from './Dial'
import { SurfaceLight } from './SurfaceLight'

const folios = ['i', 'ii', 'iii', 'iv']
const numerals = ['I', 'II', 'III', 'IV']
const catchwords = ['Likes', 'Work', 'Extras', 'Finis.']

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
      <svg aria-hidden width="0" height="0" className="absolute">
        <defs>
          <filter id="ink" x="-2%" y="-6%" width="104%" height="112%">
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="2.2" xChannelSelector="R" yChannelSelector="G" result="rough" />
            <feGaussianBlur in="rough" stdDeviation="0.45" result="soft" />
            <feComponentTransfer in="soft">
              <feFuncA type="table" tableValues="0 0.1 0.95 1" />
            </feComponentTransfer>
          </filter>
        </defs>
      </svg>
      <div aria-hidden className="leather-bg" />
      <SurfaceLight />
      <main className="fixed inset-0 overflow-y-auto text-[clamp(14px,0.4vw+1.1vh,21px)] leading-[1.55]">

        <div className="relative p-[2.2vmin]">
        <Dial />
        <div className="relative mx-auto grid min-h-[calc(100svh-4.4vmin)] w-full max-w-[1500px] grid-rows-[auto_1fr_auto] gap-[5vh] px-[5vw] py-[4.5vh]">
          <span
            aria-hidden
            className="deboss pointer-events-none absolute right-[6%] bottom-[10%] font-accent text-[clamp(8rem,26vw,26rem)] leading-none italic select-none"
          >
            {numerals[index]}
          </span>
          <Reveal>
            <header className="flex items-baseline justify-between border-b border-ink/25 pb-[0.8em]">
              <Link to="/" className="label !text-ink no-underline">
                {profile.handle}
              </Link>
            </header>
          </Reveal>

          <div key={pathname} className="grid content-center">
            {children}
          </div>

          <footer className="border-t border-ink/25 pt-[1.2em]">
            <div className="grid grid-cols-1 items-end gap-x-[4vw] gap-y-[2.4vh] md:grid-cols-12">
              <div className="md:col-span-5">
                <p className="label mb-[0.4em]">Correspondence</p>
                <CopyEmail email={profile.email} />
                <ul className="mt-[0.3em] flex gap-[1.2em]">
                  {profile.socials.map((social) => (
                    <li key={social.label}>
                      <a href={social.href} target="_blank" rel="noreferrer" className="link">
                        {social.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="md:col-span-2">
                <span aria-label="Signed oeuvars" className="signature font-script text-[3.2em] leading-none">
                  {profile.handle}
                </span>
              </div>
              <div className="md:col-span-5">
                <p className="label mb-[0.4em]">Colophon</p>
                <p className="text-[0.9em] text-ink-soft">{profile.colophon}</p>
                <p className="label mt-[0.6em]">&copy; 2026 {profile.handle}</p>
              </div>
            </div>
            <div className="mt-[1.4em] flex items-baseline justify-between text-[0.85em] text-ink-soft italic">
              <span aria-hidden>&nbsp;</span>
              <span>{folios[index]}</span>
              <span>{catchwords[index]}</span>
            </div>
          </footer>
        </div>
        </div>
      </main>
    </MotionConfig>
  )
}
