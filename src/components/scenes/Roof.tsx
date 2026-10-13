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
      <rect x={x - 24} y="98" width="48" height="52" fill={PINK} />
      <path d={`M${x - 32} 100 ${x} 78 ${x + 32} 100Z`} fill={RIDGE} />
      <path d={`M${x - 11} 150V118a11 11 0 0 1 22 0V150Z`} fill={lit ? '#f6c75a' : '#5c6c7c'} stroke={CREAM} strokeWidth="3" />
      <path d={`M${x} 107V150`} stroke={CREAM} strokeWidth="2" />
    </>
  )
}

/** The building's roof against the sky: slates, dormers and chimney pots, and a sign standing on the ridge. */
export function Roof({ sign }: RoofProps) {
  return (
    <svg viewBox="0 0 1000 150" aria-hidden className="block h-auto w-full">
      <g fill={CREAM}>
        <rect x="14" y="32" width="136" height="22" rx="11" />
        <rect x="48" y="16" width="78" height="26" rx="13" />
        <rect x="846" y="40" width="140" height="20" rx="10" />
        <rect x="882" y="26" width="72" height="24" rx="12" />
      </g>
      <path d="M770 20l8 5 8-5M800 32l6 4 6-4M184 50l7 4 7-4" fill="none" stroke="#3b1f1a" strokeWidth="2" strokeLinecap="round" />

      <path d="M10 150 46 80H954L990 150Z" fill={SLATE} />
      <path d="M35 104H965M22 128H978" stroke={RIDGE} strokeWidth="2" />
      <rect x="42" y="74" width="916" height="7" fill={RIDGE} />
      <Mirror width={1000}>
        <rect x="216" y="38" width="30" height="38" fill="#c4532a" />
        <rect x="212" y="34" width="38" height="7" fill="#a3401f" />
        <rect x="222" y="23" width="8" height="11" fill="#a3401f" />
        <rect x="233" y="23" width="8" height="11" fill="#a3401f" />
        <Dormer x={130} />
        <Dormer x={320} lit />
      </Mirror>
      <Dormer x={500} />

      {posts.map((x) => (
        <path key={x} d={`M${x} 74V58`} stroke={RED} strokeWidth="2" />
      ))}
      <rect x="296" y="56" width="408" height="4" fill={RED} />
      <Lettering x={500} y={50} text={sign} width={390} max={44} tracking={0.16} fill={RED} weight={800} />
    </svg>
  )
}
