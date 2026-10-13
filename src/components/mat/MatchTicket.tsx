import type { Like } from '../../types'
import { PROP, RENDER } from './classes'

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
 * sponsors' marks and the thermal print are in the render. The stub down the left edge starts to tear under
 * the pointer.
 */
export function MatchTicket({ like }: MatchTicketProps) {
  return (
    <article
      data-prop="ticket"
      data-linger="550"
      aria-label={`${like.subject}: ${like.title}. ${like.note}`}
      className={`${PROP} group/ticket z-2 flex h-[9.375em] w-[20.625em] [--tall:0.08]`}
    >
      <div
        aria-hidden
        className={`${RENDER} w-[3.4em] origin-top-right bg-[url(/objects/mat/ticket-stub.avif)] transition-[rotate,translate] duration-400 ease-spring group-brushed/ticket:-translate-x-[0.25em] group-brushed/ticket:translate-y-[0.15em] group-brushed/ticket:-rotate-4`}
      />
      <div className={`${RENDER} flex-1 bg-[url(/objects/mat/ticket-main.avif)]`}>
        <p className="sr-only">{PRINT.join('. ')}.</p>
      </div>
    </article>
  )
}
