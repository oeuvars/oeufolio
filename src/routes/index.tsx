import { createFileRoute } from '@tanstack/react-router'
import { MotionConfig } from 'motion/react'

import { Clock } from '../components/Clock'
import { CopyEmail } from '../components/CopyEmail'
import { HandCircle } from '../components/HandCircle'
import LightRays from '../components/LightRays'
import { PaperLight } from '../components/PaperLight'
import { QuillCursor } from '../components/QuillCursor'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/')({ component: Home })

function Home() {
  const { headline } = profile

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
      <PaperLight />
      <main className="fixed inset-0 overflow-y-auto text-[clamp(14px,0.4vw+1.1vh,21px)] leading-[1.55]">
        <div aria-hidden className="pointer-events-none fixed inset-0 opacity-30 mix-blend-screen">
          <LightRays
            raysOrigin="top-left"
            raysColor="#ffc27a"
            raysSpeed={0.4}
            lightSpread={1.1}
            rayLength={2.2}
            fadeDistance={1.1}
            noiseAmount={0.1}
            followMouse
            mouseInfluence={0.05}
          />
        </div>
        <QuillCursor />

        <div className="relative mx-auto grid min-h-full w-full max-w-[1400px] grid-rows-[auto_1fr_auto] gap-[5vh] px-[5vw] py-[4.5vh]">
          <Reveal>
            <header className="flex items-baseline justify-between border-b border-ink/25 pb-[0.8em]">
              <span className="label !text-ink">{profile.handle}</span>
              <span className="label">
                It is <Clock /> where I am
              </span>
            </header>
          </Reveal>

          <div className="grid grid-cols-1 content-center gap-x-[6vw] gap-y-[4vh] md:grid-cols-12">
            <div className="flex flex-col gap-[3.2vh] md:col-span-7">
              <Reveal delay={0.1}>
                <p className="label mb-[1.2em]">{profile.role}</p>
                <h1 className="ink text-[clamp(2.4rem,5.4vw,5.2rem)] leading-[1.02] font-normal tracking-[-0.012em] text-balance">
                  {headline.before}
                  <HandCircle>
                    <em className="font-accent text-rubric">{headline.accent}</em>
                  </HandCircle>
                  {headline.after}
                </h1>
              </Reveal>

              <Reveal delay={0.25} className="max-w-[34em] space-y-[0.7em] text-[1.12em] text-pretty">
                {profile.intro.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </Reveal>

              <Reveal delay={0.4} className="max-w-[34em]">
                <p className="label mb-[0.8em]">Questions</p>
                <dl className="space-y-[0.7em]">
                  {profile.questions.map((item) => (
                    <div key={item.q} className="grid grid-cols-[auto_1fr] gap-x-[0.8em]">
                      <dt className="label pt-[0.45em] !text-rubric">Q:</dt>
                      <dd className="italic">
                        {item.q} <span className="not-italic text-ink-soft">{item.a}</span>
                      </dd>
                    </div>
                  ))}
                </dl>
              </Reveal>
            </div>

            <div className="flex flex-col gap-[3.2vh] md:col-span-5">
              <Reveal delay={0.3}>
                <p className="label mb-[0.8em]">Selected works</p>
                <ul className="index border-t border-ink/25">
                  {profile.works.map((work, i) => (
                    <li key={work.title} className="border-b border-ink/25">
                      <a
                        href={work.href}
                        target="_blank"
                        rel="noreferrer"
                        className="block py-[0.7em] no-underline"
                      >
                        <span className="flex items-baseline gap-[0.7em]">
                          <span className="label w-[4.6em] shrink-0 whitespace-nowrap">Fig. {i + 1}</span>
                          <span className="text-[1.2em]">{work.title}</span>
                          <span className="leader" />
                          <span className="label whitespace-nowrap">
                            {work.category} ~ {work.year}
                          </span>
                        </span>
                        <span className="block pl-[6.1em] text-[0.95em] text-ink-soft">
                          {work.summary}
                        </span>
                      </a>
                    </li>
                  ))}
                </ul>
              </Reveal>

              <Reveal delay={0.5}>
                <p className="label mb-[0.8em]">Now</p>
                <p className="max-w-[30em] text-pretty">{profile.now}</p>
              </Reveal>
            </div>
          </div>

          <Reveal delay={0.6}>
            <p aria-hidden className="label mb-[1.4em] text-center !tracking-[0.9em]">
              * * *
            </p>
            <footer className="grid grid-cols-1 items-end gap-x-[4vw] gap-y-[2.4vh] border-t border-ink/25 pt-[1.2em] md:grid-cols-12">
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
            </footer>
            <div className="mt-[1.6em] flex items-baseline justify-between text-[0.85em] text-ink-soft italic">
              <span aria-hidden>&nbsp;</span>
              <span>i</span>
              <span>Finis.</span>
            </div>
          </Reveal>
        </div>
      </main>
    </MotionConfig>
  )
}
