import { createFileRoute } from '@tanstack/react-router'

import { PageTitle } from '../components/PageTitle'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/')({ component: Basics })

function Basics() {
  const { headline, intro, questions, now } = profile.basics

  return (
    <div className="grid grid-cols-1 gap-x-[4vw] gap-y-[5vh] @3xl:grid-cols-12">
      <div className="flex flex-col gap-[3.2vh] @3xl:col-span-7">
        <Reveal delay={0.1}>
          <PageTitle before={headline.before} accent={headline.accent} after={headline.after} />
        </Reveal>
        <Reveal delay={0.25} className="max-w-[34em] space-y-[0.7em] text-pretty">
          {intro.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </Reveal>
      </div>

      <div className="flex flex-col gap-[4vh] @3xl:col-span-5">
        <Reveal delay={0.35}>
          <p className="label row pb-[0.7em]">Questions</p>
          <dl>
            {questions.map((item, i) => (
              <div key={item.q} className="row grid grid-cols-[2.4em_1fr] gap-x-[0.6em] py-[0.7em]">
                <dt className="label pt-[0.3em]">Q{i + 1}</dt>
                <dd>
                  <span className="font-bold">{item.q}</span> {item.a}
                </dd>
              </div>
            ))}
          </dl>
        </Reveal>
        <Reveal delay={0.5}>
          <p className="label row pb-[0.7em]">Now</p>
          <p className="max-w-[30em] pt-[0.7em] text-pretty">{now}</p>
        </Reveal>
      </div>
    </div>
  )
}
