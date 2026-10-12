import { createFileRoute } from '@tanstack/react-router'

import { PageTitle } from '../components/PageTitle'
import { Reveal } from '../components/Reveal'
import { profile } from '../content'

export const Route = createFileRoute('/extras')({ component: Extras })

const numerals = ['I', 'II', 'III', 'IV', 'V', 'VI']

function Extras() {
  const { plates, playlist } = profile.extras

  return (
    <div className="flex flex-col gap-[5vh]">
      <Reveal delay={0.1}>
        <PageTitle before="A few " accent="extras" after="." />
      </Reveal>

      <div className="grid grid-cols-1 gap-x-[6vw] gap-y-[4vh] md:grid-cols-12">
        <Reveal delay={0.25} className="md:col-span-7">
          <p className="label mb-[0.8em]">Art and design</p>
          <ul className="grid grid-cols-2 gap-[1.4em]">
            {plates.map((plate, i) => (
              <li key={plate.title}>
                <figure>
                  <div className="grid aspect-[4/3] place-items-center border border-ink/40 bg-ink/[0.04] shadow-[inset_0_0_0_5px_rgba(255,255,255,0.12)]">
                    {plate.image ? (
                      <img src={plate.image} alt={plate.title} className="h-full w-full object-cover" />
                    ) : (
                      <span className="label">Plate {numerals[i]}</span>
                    )}
                  </div>
                  <figcaption className="mt-[0.5em] flex items-baseline justify-between gap-[1em] text-[0.9em]">
                    <span className="italic">{plate.title}</span>
                    <span className="text-ink-soft">{plate.caption}</span>
                  </figcaption>
                </figure>
              </li>
            ))}
          </ul>
        </Reveal>

        <Reveal delay={0.4} className="md:col-span-5">
          <p className="label mb-[0.8em]">Playlist</p>
          <div className="border-t border-ink/25 pt-[0.8em]">
            <p className="text-[1.25em]">{playlist.title}</p>
            <p className="mb-[0.8em] italic text-ink-soft">{playlist.note}</p>
            {playlist.embed ? (
              <iframe
                title={playlist.title}
                src={playlist.embed}
                loading="lazy"
                allow="encrypted-media"
                className="h-[352px] w-full rounded-[2px] border border-ink/30"
              />
            ) : (
              <a href={playlist.href} target="_blank" rel="noreferrer" className="link">
                Open the playlist
              </a>
            )}
          </div>
        </Reveal>
      </div>
    </div>
  )
}
