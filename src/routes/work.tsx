import { createFileRoute } from '@tanstack/react-router'

import { PageTitle } from '../components/PageTitle'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/work')({ component: Work })

function Work() {
  return (
    <div className="flex flex-col gap-[5vh]">
      <Reveal delay={0.1}>
        <PageTitle before="Where I've " accent="worked" after="." />
      </Reveal>

      <div className="grid grid-cols-1 gap-x-[6vw] gap-y-[4vh] md:grid-cols-12">
        <Reveal delay={0.25} className="md:col-span-7">
          <p className="label mb-[0.8em]">Experience</p>
          <ul className="border-t border-ink/25">
            {profile.experience.map((role) => (
              <li key={`${role.org}-${role.period}`} className="border-b border-ink/25 py-[0.8em]">
                <span className="flex items-baseline gap-[0.7em]">
                  <span className="text-[1.25em]">{role.org}</span>
                  <span className="leader" />
                  <span className="label whitespace-nowrap">{role.period}</span>
                </span>
                <span className="block italic text-ink-soft">{role.role}</span>
                <span className="block text-[0.95em]">{role.summary}</span>
              </li>
            ))}
          </ul>
        </Reveal>

        <Reveal delay={0.4} className="md:col-span-5">
          <p className="label mb-[0.8em]">Selected works</p>
          <ul className="index border-t border-ink/25">
            {profile.works.map((work, i) => (
              <li key={work.title} className="border-b border-ink/25">
                <a href={work.href} target="_blank" rel="noreferrer" className="block py-[0.7em] no-underline">
                  <span className="flex items-baseline gap-[0.7em]">
                    <span className="label w-[4.6em] shrink-0 whitespace-nowrap">Fig. {i + 1}</span>
                    <span className="text-[1.2em]">{work.title}</span>
                    <span className="leader" />
                    <span className="label whitespace-nowrap">
                      {work.category} ~ {work.year}
                    </span>
                  </span>
                  <span className="block pl-[6.1em] text-[0.95em] text-ink-soft">{work.summary}</span>
                </a>
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </div>
  )
}
