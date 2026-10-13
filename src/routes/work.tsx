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

      <div className="grid grid-cols-1 gap-x-[4vw] gap-y-[5vh] @3xl:grid-cols-12">
        <Reveal delay={0.25} className="@3xl:col-span-7">
          <p className="label row pb-[0.7em]">Experience</p>
          <ul>
            {profile.experience.map((role) => (
              <li key={`${role.org}-${role.period}`} className="row py-[0.8em]">
                <span className="flex items-baseline gap-[0.8em]">
                  <span className="display text-[1.2em]">{role.org}</span>
                  <span className="label ml-auto whitespace-nowrap">{role.period}</span>
                </span>
                <span className="block font-bold">{role.role}</span>
                <span className="block text-[0.95em]">{role.summary}</span>
              </li>
            ))}
          </ul>
        </Reveal>

        <Reveal delay={0.4} className="@3xl:col-span-5">
          <p className="label row pb-[0.7em]">Selected works</p>
          <ul>
            {profile.works.map((work, i) => (
              <li key={work.title} className="row">
                <a
                  href={work.href}
                  target="_blank"
                  rel="noreferrer"
                  className="row-link -mx-[0.6em] block px-[0.6em] py-[0.8em] no-underline"
                >
                  <span className="flex items-baseline gap-[0.8em]">
                    <span className="label w-[2.4em] shrink-0">{String(i + 1).padStart(2, '0')}</span>
                    <span className="display text-[1.1em]">{work.title}</span>
                    <span className="label ml-auto whitespace-nowrap">
                      {work.category} / {work.year}
                    </span>
                  </span>
                  <span className="block pl-[3.2em] text-[0.95em]">{work.summary}</span>
                </a>
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </div>
  )
}
