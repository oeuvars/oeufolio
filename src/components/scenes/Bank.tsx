import type { Signage } from '../../types'
import { Lettering } from './Lettering'
import { Mirror } from './Mirror'

const WALL = '#1f5a4c'
const DEEP = '#123f35'
const MARBLE = '#efe6d2'
const VEIN = '#d6ccb6'
const STEEL = '#aeb8b8'
const IRON = '#6f7a7c'
const BRASS = '#d9a52b'
const GOLD = '#f2b632'
const COCOA = '#3b1f1a'
const WOOD = '#6e2a18'

const bolts = Array.from({ length: 12 }, (_, i) => (i * Math.PI) / 6)
const spokes = [0, 45, 90, 135]
const bars = [54, 63, 72, 81, 90, 99]
const tiles = Array.from({ length: 16 }, (_, i) => i)

/**
 * A banking hall: the vault's door shut between two tellers' grilles, a marble counter with a few gold bars
 * on it, columns, and a chequered floor. The sign is the brass-framed board over the vault.
 */
export function Bank({ sign }: Signage) {
  return (
    <svg viewBox="0 0 400 400" preserveAspectRatio="xMidYMid slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="400" height="400" fill={WALL} />
      <rect y="84" width="400" height="3" fill={BRASS} />
      <rect x="80" y="40" width="240" height="30" fill={DEEP} stroke={BRASS} strokeWidth="3" />
      <Lettering x={200} y={61} text={sign} width={216} max={16} tracking={0.22} fill={GOLD} />

      <rect x="120" y="112" width="160" height="176" fill="#55606a" />
      <circle cx="200" cy="198" r="68" fill={STEEL} stroke={IRON} strokeWidth="5" />
      <circle cx="200" cy="198" r="50" fill="none" stroke="#8e9a9a" strokeWidth="3" />
      {bolts.map((angle) => (
        <circle key={angle} cx={200 + Math.cos(angle) * 59} cy={198 + Math.sin(angle) * 59} r="3" fill={IRON} />
      ))}
      {spokes.map((turn) => (
        <g key={turn} transform={`rotate(${turn} 200 198)`}>
          <path d="M172 198H228" stroke={BRASS} strokeWidth="4" strokeLinecap="round" />
          <circle cx="172" cy="198" r="3.5" fill={BRASS} />
          <circle cx="228" cy="198" r="3.5" fill={BRASS} />
        </g>
      ))}
      <circle cx="200" cy="198" r="19" fill="none" stroke={BRASS} strokeWidth="4" />
      <circle cx="200" cy="198" r="6" fill={BRASS} />
      <rect x="264" y="160" width="18" height="14" fill={IRON} />
      <rect x="264" y="222" width="18" height="14" fill={IRON} />

      <Mirror width={400}>
        <rect x="14" y="87" width="22" height="263" fill={MARBLE} />
        <path d="M21 96V342M29 96V342" stroke={VEIN} strokeWidth="2" />
        <rect x="10" y="87" width="30" height="8" fill={MARBLE} stroke={VEIN} strokeWidth="1" />
        <rect x="10" y="342" width="30" height="8" fill={MARBLE} stroke={VEIN} strokeWidth="1" />

        <path d="M76 0V44" stroke={BRASS} strokeWidth="2" />
        <circle cx="76" cy="54" r="22" fill={MARBLE} opacity="0.14" />
        <circle cx="76" cy="54" r="10" fill={MARBLE} />

        <rect x="58" y="202" width="38" height="9" fill={BRASS} />
        <rect x="44" y="214" width="66" height="84" fill={DEEP} stroke={BRASS} strokeWidth="3" />
        {bars.map((x) => (
          <path key={x} d={`M${x} 216V270`} stroke={BRASS} strokeWidth="2.5" />
        ))}
        <path d="M46 270H108" stroke={BRASS} strokeWidth="2.5" />
        <path d="M62 296V284a15 10 0 0 1 30 0V296Z" fill={COCOA} />
      </Mirror>

      <rect x="30" y="296" width="340" height="10" fill={MARBLE} />
      <rect x="38" y="306" width="324" height="44" fill={WOOD} />
      {[50, 128, 206, 284].map((x) => (
        <rect key={x} x={x} y="314" width="66" height="28" fill="none" stroke="#8a3a22" strokeWidth="2" />
      ))}
      {[
        [178, 284],
        [202, 284],
        [190, 272],
      ].map(([x, y]) => (
        <path key={`${x}-${y}`} d={`M${x} ${y + 12}l3-12h14l3 12Z`} fill={GOLD} stroke="#c98f1c" strokeWidth="1" />
      ))}

      {tiles.map((tile) => (
        <g key={tile}>
          <rect x={tile * 25} y="350" width="25" height="25" fill={tile % 2 ? COCOA : MARBLE} />
          <rect x={tile * 25} y="375" width="25" height="25" fill={tile % 2 ? MARBLE : COCOA} />
        </g>
      ))}
    </svg>
  )
}
