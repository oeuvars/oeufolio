import { Lettering } from './Lettering'
import { Mirror } from './Mirror'

const SLATE = '#6f6a80'
const RIDGE = '#57526a'
const PINK = '#f3a9b4'
const CREAM = '#fbf0d9'
const RED = '#b3291b'
const posts = Array.from({ length: 15 }, (_, i) => 304 + i * 28)

type RoofProps = {
  sign: string
}

function Dormer({ x, lit }: { x: number; lit?: boolean }) {
  return (
    <>
      <rect x={x - 26} y="122" width="52" height="68" fill={PINK} />
      <path d={`M${x - 34} 124 ${x} 98 ${x + 34} 124Z`} fill={RIDGE} />
      <path d={`M${x - 13} 190V148a13 13 0 0 1 26 0V190Z`} fill={lit ? '#f6c75a' : '#5c6c7c'} stroke={CREAM} strokeWidth="3" />
      <path d={`M${x} 136V190`} stroke={CREAM} strokeWidth="2" />
    </>
  )
}

/** The building's roof against the sky: slates, dormers and chimney pots, and a sign standing on the ridge. */
export function Roof({ sign }: RoofProps) {
  return (
    <svg viewBox="0 0 1000 190" aria-hidden className="block h-auto w-full">
      <rect x="-30" y="34" width="150" height="24" rx="12" fill={CREAM} opacity="0.85" />
      <rect x="30" y="16" width="110" height="26" rx="13" fill={CREAM} opacity="0.85" />
      <rect x="850" y="48" width="170" height="22" rx="11" fill={CREAM} opacity="0.85" />
      <path d="M770 26l8 5 8-5M800 40l6 4 6-4M196 60l7 4 7-4" fill="none" stroke="#3b1f1a" strokeWidth="2" strokeLinecap="round" />

      <path d="M10 190 52 96H948L990 190Z" fill={SLATE} />
      <path d="M38 128H962M24 160H976" stroke={RIDGE} strokeWidth="2" />
      <rect x="48" y="90" width="904" height="7" fill={RIDGE} />
      <Mirror width={1000}>
        <rect x="216" y="50" width="30" height="42" fill="#c4532a" />
        <rect x="212" y="46" width="38" height="7" fill="#a3401f" />
        <rect x="222" y="34" width="8" height="12" fill="#a3401f" />
        <rect x="233" y="34" width="8" height="12" fill="#a3401f" />
        <Dormer x={130} />
        <Dormer x={320} lit />
      </Mirror>
      <Dormer x={500} />

      {posts.map((x) => (
        <path key={x} d={`M${x} 90V72`} stroke={RED} strokeWidth="2" />
      ))}
      <rect x="296" y="70" width="408" height="4" fill={RED} />
      <Lettering x={500} y={64} text={sign} width={390} max={50} tracking={0.16} fill={RED} weight={800} />
    </svg>
  )
}
