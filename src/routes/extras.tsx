import { createFileRoute } from '@tanstack/react-router'

import { BusinessCard } from '../components/mat/BusinessCard'
import { KeyBunch } from '../components/mat/KeyBunch'
import { Mat } from '../components/mat/Mat'
import { MatchTicket } from '../components/mat/MatchTicket'
import { RecordSleeve } from '../components/mat/RecordSleeve'
import { Recorder } from '../components/mat/Recorder'
import { Wallet } from '../components/mat/Wallet'
import { profile } from '../content'

export const Route = createFileRoute('/extras')({ component: Extras })

/**
 * The extras, as what was left on a desk: a teal leather cutting mat seen from overhead, with the things I
 * like lying on it, rendered as one photograph, my business card among them. The shaving cream, the razor
 * and the picks are only in the picture. The mat is the page, and the page is the whole strip. The page's
 * own margins are given over to it: the ones undone here are SiteShell's padding round a page, up to where
 * the strip before this one lies over it, and the band beside it. The sports cars like has no object of its
 * own: it is the car key on the bunch that carries the name.
 */
function Extras() {
  const { name, likes, playlist } = profile.extras

  return (
    <>
      <h1 className="sr-only">Extras</h1>
      <Mat className="-mt-[6.4vh] -mr-[calc(clamp(1rem,2.6vw,3rem)+1.4rem)] -mb-[4vh] -ml-[2.5rem] min-h-screen md:-mr-[calc(clamp(1rem,2.6vw,3rem)+1.9rem)] md:-mb-[6.4vh] md:-ml-[3.1rem]">
        <KeyBunch name={name} car={likes.key} />
        <BusinessCard name={name} />
        <RecordSleeve like={likes.record} playlist={playlist} />
        <Recorder like={likes.recorder} />
        <MatchTicket like={likes.ticket} />
        <Wallet />
      </Mat>
    </>
  )
}
