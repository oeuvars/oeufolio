import type { Signage } from '../../types'
import { Lettering } from './Lettering'

const WALL = '#c7d5d3'
const RIB = '#b2c4c1'
const FLOOR = '#b9ad98'
const UPRIGHT = '#3f73a8'
const BEAM = '#e0782a'
const CREAM = '#fbf0d9'
const COCOA = '#3b1f1a'
const YELLOW = '#f2b632'
const cartons = ['#c98b4a', '#d9a05b', '#b97a3c', '#f3a9b4']

const ribs = Array.from({ length: 19 }, (_, i) => 20 + i * 20)
/** The racking's shelves, top to bottom: the height of each beam, and the cartons on it in its two bays. */
const shelves = [
  { y: 150, bays: [[[44, 40, 0], [40, 30, 1], [48, 46, 2]], [[50, 34, 1], [36, 44, 0], [46, 28, 3]]] },
  { y: 218, bays: [[[60, 44, 1], [70, 36, 0]], [[38, 46, 2], [38, 46, 2], [52, 30, 1]]] },
  { y: 286, bays: [[[48, 48, 3], [40, 36, 0], [44, 42, 1]], [[70, 50, 0], [60, 38, 2]]] },
]

type CartonProps = {
  x: number
  y: number
  w: number
  h: number
  fill: string
}

function Carton({ x, y, w, h, fill }: CartonProps) {
  return (
    <>
      <rect x={x} y={y} width={w} height={h} fill={fill} stroke="#8a5a2c" strokeWidth="1" />
      <rect x={x + w / 2 - 2} y={y} width="4" height={h} fill="#8a5a2c" opacity="0.35" />
      <rect x={x + 4} y={y + 6} width="11" height="7" fill={CREAM} />
    </>
  )
}

/**
 * A warehouse: pallet racking full of cartons under a corrugated wall, a pallet waiting on the floor, and a
 * forklift with one more carton on its forks. The sign hangs from the roof.
 */
export function Warehouse({ sign }: Signage) {
  return (
    <svg viewBox="0 0 400 400" preserveAspectRatio="xMidYMid slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="400" height="400" fill={WALL} />
      {ribs.map((x) => (
        <path key={x} d={`M${x} 0V350`} stroke={RIB} strokeWidth="2" />
      ))}
      <rect y="350" width="400" height="50" fill={FLOOR} />
      <rect y="364" width="400" height="5" fill={YELLOW} />

      <path d="M110 0V44M290 0V44" stroke={COCOA} strokeWidth="2" />
      <rect x="80" y="44" width="240" height="30" fill={UPRIGHT} />
      <Lettering x={200} y={65} text={sign} width={216} max={17} tracking={0.22} fill={CREAM} />

      {shelves.map(({ y, bays }) =>
        bays.map((bay, side) => {
          let x = (side ? 206 : 46) + 4

          return bay.map(([w, h, colour], i) => {
            const carton = <Carton key={`${y}-${side}-${i}`} x={x} y={y - h} w={w} h={h} fill={cartons[colour]} />
            x += w + 4

            return carton
          })
        }),
      )}
      {shelves.map(({ y }) => (
        <rect key={y} x="36" y={y} width="328" height="7" fill={BEAM} />
      ))}
      {[36, 196, 356].map((x) => (
        <rect key={x} x={x} y="96" width="8" height="254" fill={UPRIGHT} />
      ))}

      <rect x="56" y="340" width="84" height="4" fill="#a9743c" />
      {[58, 96, 132].map((x) => (
        <rect key={x} x={x} y="344" width="6" height="6" fill="#a9743c" />
      ))}
      <Carton x={60} y={304} w={36} h={36} fill={cartons[1]} />
      <Carton x={98} y={304} w={36} h={36} fill={cartons[0]} />

      {/* The forklift. */}
      <rect x="298" y="296" width="5" height="50" fill={COCOA} />
      <rect x="303" y="340" width="34" height="3" fill={COCOA} />
      <Carton x={306} y={312} w={28} h={28} fill={cartons[2]} />
      <path d="M246 316V298H284V316" fill="none" stroke={COCOA} strokeWidth="3" />
      <rect x="236" y="316" width="62" height="26" rx="4" fill={YELLOW} stroke={COCOA} strokeWidth="1.5" />
      <rect x="256" y="306" width="14" height="10" rx="2" fill={COCOA} />
      {[250, 284].map((x) => (
        <g key={x}>
          <circle cx={x} cy="343" r="8" fill={COCOA} />
          <circle cx={x} cy="343" r="3" fill="#8a8a86" />
        </g>
      ))}
    </svg>
  )
}
