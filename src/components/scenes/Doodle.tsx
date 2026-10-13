import type { Room } from '../../types'

type DoodleProps = {
  /** The kind of place the company is, which is what gets drawn. */
  room: Room
  /** Each kind has two drawings, one for either end of the board. */
  second?: boolean
}

const bars = [11, 14.5, 17, 21, 23.5, 27, 29.5]

/** A carton, taped shut. */
const carton = <path d="M20 4 36 12V28L20 36 4 28V12ZM4 12l16 8 16-8M20 20v16M12 8l16 8v6" />

/** A forklift with a carton up on its forks. */
const forklift = (
  <>
    <path d="M6 21h16v10H6ZM9 21v-10h9l3 10M27 6v26M27 30h10M29 20h8v9h-8Z" />
    <circle cx="10.500" cy="33" r="3" />
    <circle cx="19.500" cy="33" r="3" />
  </>
)

/** A bank, with its columns and its pediment. */
const bank = <path d="M4 14 20 4l16 10ZM6 17.500h28M10 18v14M16.500 18v14M23.500 18v14M30 18v14M6 33h28M3 37h34" />

/** A stack of coins, and one more beside it. */
const coins = (
  <>
    <ellipse cx="16" cy="9" rx="11" ry="4.500" />
    <path d="M5 9v6c0 2.500 5 4.500 11 4.500s11-2 11-4.500V9M5 15v6c0 2.500 5 4.500 11 4.500s11-2 11-4.500v-6M5 21v6c0 2.500 5 4.500 11 4.500s11-2 11-4.500v-6" />
    <circle cx="32" cy="31" r="5.500" />
    <path d="M32 28.500v5" />
  </>
)

/** A delivery van, in a hurry. */
const van = (
  <>
    <path d="M10 10h17v18H10ZM27 16h6l5 6v6H27M30 19.500h2.500l2.500 3.500h-5ZM1 14h5M0 19h6M2 24h4" />
    <circle cx="16" cy="30" r="3.300" />
    <circle cx="32" cy="30" r="3.300" />
  </>
)

/** A shipping label, with its barcode. */
const label = (
  <>
    <path d="M5 7h30v26H5ZM9 12h12M9 16h8" />
    {bars.map((x, i) => (
      <path key={x} d={`M${x} 21v8`} strokeWidth={i % 3 ? 1.6 : 2.8} />
    ))}
  </>
)

const drawings = { warehouse: [carton, forklift], bank: [bank, coins], dock: [van, label] }

/** A small drawing chalked at one end of a board, as a café's has, of something from the company's trade. */
export function Doodle({ room, second }: DoodleProps) {
  return (
    <svg viewBox="0 0 40 40" aria-hidden fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="block h-auto w-full overflow-visible">
      {drawings[room][second ? 1 : 0]}
    </svg>
  )
}
