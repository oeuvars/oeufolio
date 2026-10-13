import { createFileRoute } from '@tanstack/react-router'

import { Earphones } from '../components/mat/Earphones'
import { IdCard } from '../components/mat/IdCard'
import { KeyBunch } from '../components/mat/KeyBunch'
import { Mat } from '../components/mat/Mat'
import { MatchTicket } from '../components/mat/MatchTicket'
import { FinPick, WedgePick } from '../components/mat/Picks'
import { RecordSleeve } from '../components/mat/RecordSleeve'
import { Recorder } from '../components/mat/Recorder'
import { SafetyRazor } from '../components/mat/SafetyRazor'
import { ShavingCream } from '../components/mat/ShavingCream'
import { Wallet } from '../components/mat/Wallet'
import { profile } from '../content'

export const Route = createFileRoute('/extras')({ component: Extras })

/**
 * The extras, as what was left on a desk: a yellow leather cutting mat seen from overhead, with the things
 * I like lying on it as renders. The mat is the page, and the page is the whole strip. The
 * page's own margins are given over to it: the ones undone here are SiteShell's padding round a page, up to
 * where the strip before this one lies over it, and the band beside it. The sports cars like has no object
 * of its own: it is the car key on the bunch that carries the name.
 */
function Extras() {
  const { name, career, company, particulars, likes, playlist } = profile.extras

  return (
    <>
      <h1 className="sr-only">Extras</h1>
      <Mat className="-mt-[6.4vh] -mr-[calc(clamp(1rem,2.6vw,3rem)+1.4rem)] -mb-[4vh] -ml-[2.5rem] min-h-screen md:-mr-[calc(clamp(1rem,2.6vw,3rem)+1.9rem)] md:-mb-[6.4vh] md:-ml-[3.1rem]">
        <KeyBunch name={name} career={career} company={company} car={likes.key} />
        <IdCard particulars={particulars} />
        <RecordSleeve like={likes.record} playlist={playlist} />
        <Recorder like={likes.recorder} />
        <MatchTicket like={likes.ticket} />
        <ShavingCream />
        <SafetyRazor />
        <Earphones />
        <Wallet />
        <FinPick />
        <WedgePick />
      </Mat>
    </>
  )
}
