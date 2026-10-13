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
        <ul className="grid grid-cols-1 border-t border-ink/30 @3xl:grid-cols-2 @3xl:gap-x-[4vw]">
          {profile.likes.map((like) => (
            <li key={like.title} className="row py-[0.9em]">
              <span className="flex flex-wrap items-baseline gap-x-[0.8em]">
                <span className="display text-[1.35em]">{like.title}</span>
                <span className="label ml-auto whitespace-nowrap">{like.tag}</span>
              </span>
              <p>{like.note}</p>
              {like.details && (
                <ul className="mt-[0.5em]">
                  {like.details.map((detail) => (
                    <li key={detail} className="flex gap-[0.8em]">
                      <span aria-hidden>+</span>
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
