import { profile } from '../../content'
import { BusinessCard } from './business-card'
import { KeyBunch } from './key-bunch'
import { Mat } from './mat'
import { MatchTicket } from './match-ticket'
import { RecordSleeve } from './record-sleeve'
import { Recorder } from './recorder'
import { Wallet } from './wallet'

/**
 * The extras, as what was left on a desk: a teal leather cutting mat seen from overhead, with the things I
 * like lying on it, rendered as one photograph, my business card among them. The shaving cream, the razor,
 * the picks, the Seiko Alpinist and the mug of coffee are only in the picture. The mat is the page, and the page is the whole
 * strip. The page's own margins are given over to it: the ones undone here are SiteShell's padding round a
 * page, up to where the strip before this one lies over it, and the band beside it. The sports cars like has no object of its
 * own: it is the car key on the bunch that carries the name. SiteShell keeps the desk in its strip, open or
 * folded, so it is laid once and the strip only uncovers and covers it. Given a band, it is only the band plate, a
 * few of the things on the desk in a row along a folded phone strip, that many pixels deep, with nothing on it to take.
 */
export const Desk = ({ band }: { band?: number }) => {
  const { name, likes, playlist } = profile.extras

  if (band) return <Mat band={band} className="h-full" />

  return (
    <Mat className="h-(--page-room) md:-mt-[6.4vh] md:-mr-[calc(clamp(1rem,2.6vw,3rem)+1.9rem)] md:-mb-[6.4vh] md:-ml-[3.1rem] md:h-auto md:min-h-screen">
      <KeyBunch name={name} car={likes.key} />
      <BusinessCard name={name} />
      <RecordSleeve like={likes.record} playlist={playlist} />
      <Recorder like={likes.recorder} />
      <MatchTicket like={likes.ticket} />
      <Wallet />
    </Mat>
  )
}
