import type { Like } from '../../types'
import { PROP } from './classes'

type MatchTicketProps = {
  like: Like
}

// The thermal print, as the club's ticket for the 2013-14 season has it. The fixture is the league match of
// 1 September 2013. The block, row, seat and turnstile are those of a real ticket of that season, and the
// price is the club's for that part of the ground at a category A match.
const PRINT = [
  'Barclays Premier League',
  'Arsenal v Tottenham Hotspur',
  '01 Sep, 2013',
  'Kick Off: 16:00',
  'Block 20 Lower Tier',
  'Row: 10',
  'Seat: 630',
  '£ 62.00',
  'Enter via: Clock End Turnstile K',
  'Adult',
]

/**
 * The Arsenal like: the club's paper match ticket. The card, the bands, the crest, the lettering, the
 * sponsors' marks and the thermal print are in the plate, and the print is here for readers.
 */
export const MatchTicket = ({ like }: MatchTicketProps) => {
  return (
    <article data-prop="ticket" aria-label={`${like.subject}: ${like.title}. ${like.note}`} className={`${PROP} z-2 h-[9.375em] w-[20.625em]`}>
      <p className="sr-only">{PRINT.join('. ')}.</p>
    </article>
  )
}
