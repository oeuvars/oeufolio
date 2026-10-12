import { createFileRoute } from '@tanstack/react-router'

import { PageTitle } from '../components/PageTitle'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/likes')({ component: Likes })

function Likes() {
  return (
    <div className="flex flex-col gap-[5vh]">
      <Reveal delay={0.1}>
        <PageTitle before="Things I " accent="like" after="." />
      </Reveal>

      <Reveal delay={0.25}>
        <ul className="grid grid-cols-1 border-t border-ink/25 md:grid-cols-2 md:gap-x-[6vw]">
          {profile.likes.map((like, i) => (
            <li key={like.title} className="border-b border-ink/25 py-[1em]">
              <span className="flex items-baseline gap-[0.7em]">
                <span className="label w-[4.6em] shrink-0 whitespace-nowrap">Fig. {i + 1}</span>
                <span className="text-[1.5em]">{like.title}</span>
                <span className="leader" />
                <span className="label whitespace-nowrap">{like.tag}</span>
              </span>
              <p className="pl-[5.3em] text-ink-soft italic">{like.note}</p>
              {like.details && (
                <ul className="mt-[0.5em] space-y-[0.15em] pl-[5.3em]">
                  {like.details.map((detail) => (
                    <li key={detail} className="flex items-baseline gap-[0.6em]">
                      <span aria-hidden className="text-rubric">
                        &#10086;
                      </span>
                      {detail}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </Reveal>
    </div>
  )
}
