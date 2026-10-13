const SKY = '#a9cdd0'
const CLOUD = '#eef0e2'
const SEA = '#5f9ea3'
const ROCK = '#5d6149'
const WHITE = '#f6efe2'
const RED = '#b3291b'
const IRON = '#3b1f1a'
const LAMP = '#f7d76a'

/** The tower narrows as it climbs: half its width at this height. */
const half = (y: number) => 22 + ((y - 380) / 500) * 14
const bands = [380, 480, 580, 680, 780]

/** A banded lighthouse on its rock, tall enough to fill a folded strip. It is cropped at the sides to fit. */
export function Lighthouse() {
  return (
    <svg viewBox="0 0 200 1000" preserveAspectRatio="xMidYMax slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="200" height="1000" fill={SKY} />
      <rect x="-20" y="150" width="92" height="20" rx="10" fill={CLOUD} />
      <rect x="14" y="134" width="66" height="22" rx="11" fill={CLOUD} />
      <rect x="128" y="246" width="96" height="18" rx="9" fill={CLOUD} />
      <path d="M52 300l7 5 7-5M136 190l6 4 6-4M150 208l5 3 5-3" fill="none" stroke={IRON} strokeWidth="1.5" strokeLinecap="round" />

      <rect y="880" width="200" height="120" fill={SEA} />
      <path d="M0 900h200M0 930h200M0 962h200" stroke="#7fb4b6" strokeWidth="1.5" strokeDasharray="14 22" />

      {bands.map((y, i) => (
        <path
          key={y}
          d={`M${100 - half(y)} ${y}H${100 + half(y)}L${100 + half(y + 100)} ${y + 100}H${100 - half(y + 100)}Z`}
          fill={i % 2 ? WHITE : RED}
        />
      ))}
      <rect x="93" y="700" width="14" height="22" rx="7" fill={IRON} />
      <rect x="94" y="510" width="12" height="20" rx="6" fill={IRON} />
      <path d="M88 880V846a12 12 0 0 1 24 0V880Z" fill={IRON} />

      <rect x="66" y="372" width="68" height="8" fill={IRON} />
      <path d="M68 372V352H132V372M84 352V372M100 352V372M116 352V372" fill="none" stroke={IRON} strokeWidth="2" />
      <rect x="82" y="318" width="36" height="54" fill={LAMP} stroke={IRON} strokeWidth="2.5" />
      <path d="M94 318V372M106 318V372" stroke={IRON} strokeWidth="1.5" />
      <path d="M76 318 100 286 124 318Z" fill={RED} />
      <path d="M100 286V262" stroke={IRON} strokeWidth="2" />
      <circle cx="100" cy="284" r="4" fill={IRON} />

      <path d="M0 1000V900L36 872 70 884 100 870 134 886 168 874 200 902V1000Z" fill={ROCK} />
    </svg>
  )
}
