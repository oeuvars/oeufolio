import { createFileRoute } from '@tanstack/react-router'

import { PageTitle } from '../components/PageTitle'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/')({ component: Basics })

function Basics() {
  const { headline, intro, questions, now } = profile.basics

  return (
    <div className="grid grid-cols-1 gap-x-[6vw] gap-y-[4vh] md:grid-cols-12">
      <div className="flex flex-col gap-[3.2vh] md:col-span-7">
        <Reveal delay={0.1}>
          <PageTitle before={headline.before} accent={headline.accent} after={headline.after} circled />
        </Reveal>
        <Reveal delay={0.25} className="max-w-[34em] space-y-[0.7em] text-[1.12em] text-pretty">
          {intro.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </Reveal>
      </div>

      <div className="flex flex-col gap-[3.2vh] md:col-span-5">
        <Reveal delay={0.35}>
          <p className="label mb-[0.8em]">Questions</p>
          <dl className="space-y-[0.7em]">
            {questions.map((item) => (
              <div key={item.q} className="grid grid-cols-[auto_1fr] gap-x-[0.8em]">
                <dt className="label pt-[0.45em] !text-rubric">Q:</dt>
                <dd className="italic">
                  {item.q} <span className="not-italic text-ink-soft">{item.a}</span>
                </dd>
              </div>
            ))}
          </dl>
        </Reveal>
        <Reveal delay={0.5}>
          <p className="label mb-[0.8em]">Now</p>
          <p className="max-w-[30em] text-pretty">{now}</p>
        </Reveal>
      </div>
    </div>
  )
}
