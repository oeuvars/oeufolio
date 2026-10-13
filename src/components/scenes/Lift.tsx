const WALL = '#a3301f'
const DOOR = '#c4532a'
const DOOR_LINE = '#d96e3e'
const CREAM = '#fbf0d9'
const BRASS = '#d9a52b'
const COCOA = '#3b1f1a'

type LiftProps = {
  /** Whether the car is at this floor, with its doors open and its gate half across. */
  open: boolean
}

const lattice = [0, 1, 2, 3, 4]
const panels = [
  [25, 81],
  [56, 81],
  [25, 134],
  [56, 134],
]

/** The lift's doors on a landing, under a lamp. */
export function Lift({ open }: LiftProps) {
  return (
    <svg viewBox="0 0 100 212" preserveAspectRatio="xMidYMax slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="100" height="212" fill={WALL} />
      <rect y="188" width="100" height="24" fill="#4f342a" />
      <circle cx="50" cy="34" r="22" fill={CREAM} opacity="0.14" />
      <rect x="47.5" y="42" width="5" height="12" fill={BRASS} />
      <rect x="42" y="53" width="16" height="3" fill={BRASS} />
      <circle cx="50" cy="34" r="9" fill={CREAM} />

      <rect x="13" y="66" width="74" height="122" fill={BRASS} />
      {open ? (
        <>
          <rect x="20" y="73" width="60" height="115" fill="#f7d76a" />
          <rect x="28" y="82" width="44" height="58" fill="none" stroke="#e0a12e" strokeWidth="2" />
          <path d="M20 158H80" stroke="#e0a12e" strokeWidth="3" />
          {lattice.map((bar) => (
            <path key={bar} d={`M20 ${73 + bar * 23}l22 11.5l-22 11.5`} fill="none" stroke={COCOA} strokeWidth="1.5" />
          ))}
          <path d="M42 73V188" stroke={COCOA} strokeWidth="2" />
        </>
      ) : (
        <>
          <rect x="20" y="73" width="29" height="115" fill={DOOR} />
          <rect x="51" y="73" width="29" height="115" fill={DOOR} />
          {panels.map(([x, y]) => (
            <rect key={`${x}-${y}`} x={x} y={y} width="19" height="46" fill="none" stroke={DOOR_LINE} strokeWidth="1.5" />
          ))}
        </>
      )}
      <circle cx="93.5" cy="130" r="2.5" fill={BRASS} />
    </svg>
  )
}
