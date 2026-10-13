import type { Signage } from '../../types'
import { Lettering } from './Lettering'

const WALL = '#8fb39a'
const FLOOR = '#b9ad98'
const CREAM = '#fbf0d9'
const COCOA = '#3b1f1a'
const IRON = '#6f7a7c'
const RED = '#b3291b'
const YELLOW = '#f2b632'

const slats = Array.from({ length: 7 }, (_, i) => 113 + i * 9)
const rollers = Array.from({ length: 19 }, (_, i) => 2 + i * 22)
const parcels = [
  [22, 280, 48, 38, '#c98b4a'],
  [74, 296, 30, 22, '#d9a05b'],
  [300, 290, 40, 28, '#f3a9b4'],
  [344, 274, 36, 44, '#b97a3c'],
] as const

/**
 * A loading dock: parcels coming down a conveyor, and the shutter half up on a van backed in to take them.
 * The sign is the board over the door.
 */
export function Dock({ sign }: Signage) {
  return (
    <svg viewBox="0 0 400 400" preserveAspectRatio="xMidYMid slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="400" height="400" fill={WALL} />
      <rect y="356" width="400" height="44" fill={FLOOR} />
      <rect y="376" width="400" height="5" fill={YELLOW} />
      <rect x="80" y="40" width="240" height="30" fill={RED} />
      <Lettering x={200} y={61} text={sign} width={216} max={17} tracking={0.22} fill={CREAM} />

      <rect x="30" y="140" width="46" height="62" fill={CREAM} stroke={COCOA} strokeWidth="1.5" />
      <rect x="44" y="134" width="18" height="10" rx="2" fill={IRON} />
      <path d="M38 158H68M38 168H68M38 178H60M38 188H64" stroke="#c9b48a" strokeWidth="2" />
      <circle cx="348" cy="166" r="22" fill={CREAM} stroke={COCOA} strokeWidth="2.5" />
      <path d="M348 166V152M348 166 358 172" stroke={COCOA} strokeWidth="2.5" strokeLinecap="round" />

      <rect x="104" y="96" width="192" height="260" fill="#55606a" />
      <rect x="112" y="104" width="176" height="252" fill="#a9d6d0" />
      <rect x="112" y="300" width="176" height="56" fill="#d9c8a4" />

      {/* The van, backed up to the door. */}
      <rect x="142" y="326" width="22" height="20" rx="4" fill={COCOA} />
      <rect x="236" y="326" width="22" height="20" rx="4" fill={COCOA} />
      <rect x="136" y="200" width="128" height="120" rx="8" fill={CREAM} stroke={COCOA} strokeWidth="2.5" />
      <rect x="146" y="210" width="46" height="34" rx="4" fill="#5c6c7c" />
      <rect x="208" y="210" width="46" height="34" rx="4" fill="#5c6c7c" />
      <rect x="137" y="258" width="126" height="10" fill={RED} />
      <path d="M200 204V318" stroke={COCOA} strokeWidth="2" />
      <rect x="191" y="278" width="5" height="12" rx="2" fill={IRON} />
      <rect x="204" y="278" width="5" height="12" rx="2" fill={IRON} />
      <rect x="141" y="286" width="10" height="16" fill={RED} />
      <rect x="249" y="286" width="10" height="16" fill={RED} />
      <rect x="186" y="298" width="28" height="10" fill={YELLOW} />
      <rect x="130" y="316" width="140" height="10" rx="3" fill={IRON} />

      <rect x="112" y="104" width="176" height="72" fill="#c7d5d3" />
      {slats.map((y) => (
        <path key={y} d={`M112 ${y}H288`} stroke="#9fb0ae" strokeWidth="1.5" />
      ))}
      <rect x="112" y="174" width="176" height="7" fill={IRON} />

      {[40, 200, 360].map((x) => (
        <rect key={x} x={x - 3} y="342" width="6" height="26" fill={IRON} />
      ))}
      {parcels.map(([x, y, w, h, fill]) => (
        <g key={x}>
          <rect x={x} y={y} width={w} height={h} fill={fill} stroke="#8a5a2c" strokeWidth="1" />
          <rect x={x + w / 2 - 2} y={y} width="4" height={h} fill="#8a5a2c" opacity="0.35" />
          <rect x={x + 4} y={y + 6} width="11" height="7" fill={CREAM} />
        </g>
      ))}
      <rect y="318" width="400" height="9" fill="#2b2a2a" />
      {rollers.map((x) => (
        <circle key={x} cx={x} cy="333" r="5" fill="#8a8a86" stroke="#2b2a2a" strokeWidth="1" />
      ))}
      <rect y="338" width="400" height="5" fill={IRON} />
    </svg>
  )
}
