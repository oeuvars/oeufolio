const WALL = '#a3301f'
const DOOR = '#c4532a'
const DOOR_LINE = '#d96e3e'
const CREAM = '#fbf0d9'
const BRASS = '#d9a52b'
const COCOA = '#3b1f1a'

type LiftProps = {
  /** The floor's number, on the plate over the doors. */
  part: number
  /** Whether the car is at this floor, with its doors open and its gate half across. */
  open: boolean
}

const lattice = [0, 1, 2, 3, 4, 5, 6, 7]

/** The lift's doors on a landing, with the floor's number over them. */
export function Lift({ part, open }: LiftProps) {
  return (
    <svg viewBox="0 0 100 400" preserveAspectRatio="xMidYMax slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="100" height="400" fill={WALL} />
      <rect y="350" width="100" height="50" fill="#4f342a" />
      <text x="51.5" y="94" textAnchor="middle" fontSize="9" fontWeight="700" letterSpacing="0.3em" fill={CREAM} className="font-futura">
        PART
      </text>
      <circle cx="50" cy="128" r="22" fill={CREAM} stroke={BRASS} strokeWidth="3.5" />
      <text x="50" y="138" textAnchor="middle" fontSize="28" fontWeight="800" fill={COCOA} className="font-futura">
        {part}
      </text>

      <rect x="13" y="168" width="74" height="182" fill={BRASS} />
      {open ? (
        <>
          <rect x="20" y="176" width="60" height="174" fill="#f7d76a" />
          <rect x="28" y="188" width="44" height="90" fill="none" stroke="#e0a12e" strokeWidth="2" />
          <path d="M20 300H80" stroke="#e0a12e" strokeWidth="3" />
          {lattice.map((bar) => (
            <path key={bar} d={`M20 ${176 + bar * 22}l22 22l-22 22`} fill="none" stroke={COCOA} strokeWidth="1.5" />
          ))}
          <path d="M42 176V350" stroke={COCOA} strokeWidth="2" />
        </>
      ) : (
        <>
          <rect x="20" y="176" width="29" height="174" fill={DOOR} />
          <rect x="51" y="176" width="29" height="174" fill={DOOR} />
          <rect x="25" y="186" width="19" height="70" fill="none" stroke={DOOR_LINE} strokeWidth="1.5" />
          <rect x="56" y="186" width="19" height="70" fill="none" stroke={DOOR_LINE} strokeWidth="1.5" />
          <rect x="25" y="266" width="19" height="74" fill="none" stroke={DOOR_LINE} strokeWidth="1.5" />
          <rect x="56" y="266" width="19" height="74" fill="none" stroke={DOOR_LINE} strokeWidth="1.5" />
        </>
      )}
      <circle cx="93.5" cy="262" r="2.5" fill={BRASS} />
    </svg>
  )
}
