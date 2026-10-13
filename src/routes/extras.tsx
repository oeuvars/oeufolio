import { createFileRoute } from '@tanstack/react-router'

import { PageTitle } from '../components/PageTitle'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/extras')({ component: Extras })

function Extras() {
  const { plates, playlist } = profile.extras

  return (
    <div className="flex flex-col gap-[5vh]">
      <Reveal delay={0.1}>
        <PageTitle before="A few " accent="extras" after="." />
      </Reveal>

      <div className="grid grid-cols-1 gap-x-[4vw] gap-y-[5vh] @3xl:grid-cols-12">
        <Reveal delay={0.25} className="@3xl:col-span-7">
          <p className="label row pb-[0.7em]">Art and design</p>
          <ul className="grid grid-cols-2 gap-[1.4em] pt-[1em]">
            {plates.map((plate, i) => (
              <li key={plate.title}>
                <figure>
                  <div className="frame grid aspect-[4/3] place-items-center bg-ink/[0.06]">
                    {plate.image ? (
                      <img src={plate.image} alt={plate.title} className="h-full w-full object-cover" />
                    ) : (
                      <span className="label">IMG_{String(i + 1).padStart(2, '0')}</span>
                    )}
                  </div>
                  <figcaption className="mt-[0.5em] flex items-baseline justify-between gap-[1em] text-[0.9em]">
                    <span className="font-bold">{plate.title}</span>
                    <span>{plate.caption}</span>
                  </figcaption>
                </figure>
              </li>
            ))}
          </ul>
        </Reveal>

        <Reveal delay={0.4} className="@3xl:col-span-5">
          <p className="label row pb-[0.7em]">Playlist</p>
          <div className="pt-[0.8em]">
            <p className="display text-[1.2em]">{playlist.title}</p>
            <p className="mb-[0.8em]">{playlist.note}</p>
            {playlist.embed ? (
              <iframe
                title={playlist.title}
                src={playlist.embed}
                loading="lazy"
                allow="encrypted-media"
                className="h-[352px] w-full border border-ink/40"
              />
            ) : (
              <a href={playlist.href} target="_blank" rel="noreferrer" className="label link">
                Open the playlist
              </a>
            )}
          </div>
        </Reveal>
      </div>
    </div>
  )
}
