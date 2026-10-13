import type { Signage } from '../../types'
import { Lettering } from './Lettering'

const WALL = '#7d8f4f'
const FLOOR = '#4f342a'
const CASE = '#9a4f2a'
const DRAWER = '#b5622f'
const CREAM = '#fbf0d9'
const BRASS = '#d9a52b'
const PINK = '#f3a9b4'
const BLUE = '#3f73a8'

const rows = [0, 1, 2, 3, 4, 5]
const columns = [0, 1, 2, 3, 4, 5, 6, 7]
const rungs = [0, 1, 2, 3, 4, 5, 6]

/**
 * The archive: a wall of card drawers with a ladder on a rail to reach the top ones, and a stack of cake
 * boxes somebody has left. The sign is carved along the top of the case.
 */
export function Archive({ sign }: Signage) {
  return (
    <svg viewBox="0 0 480 400" preserveAspectRatio="xMidYMax slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="480" height="400" fill={WALL} />
      <rect y="350" width="480" height="50" fill={FLOOR} />
      <path d="M0 367H480M0 384H480" stroke="#3d271f" strokeWidth="1.5" />

      {[110, 370].map((x) => (
        <g key={x}>
          <path d={`M${x} 0V20`} stroke={BRASS} strokeWidth="2" />
          <path d={`M${x - 16} 36l8-16h16l8 16Z`} fill={CREAM} />
        </g>
      ))}

      <rect x="40" y="58" width="400" height="36" fill="#7a3a1e" />
      <Lettering x={240} y={83} text={sign} width={360} max={18} tracking={0.24} fill={CREAM} />
      <rect x="48" y="94" width="384" height="256" fill={CASE} />
      {rows.map((row) =>
        columns.map((column) => {
          const x = 54.5 + column * 47
          const y = 102 + row * 41

          return (
            <g key={`${row}-${column}`}>
              <rect x={x} y={y} width="42" height="36" fill={DRAWER} stroke="#7a3a1e" strokeWidth="1" />
              <rect x={x + 11} y={y + 7} width="20" height="9" fill={(row * 3 + column * 5) % 11 === 2 ? '#b3291b' : CREAM} />
              <circle cx={x + 21} cy={y + 26} r="3.5" fill={BRASS} />
            </g>
          )
        }),
      )}

      <path d="M30 54H450" stroke={BRASS} strokeWidth="4" strokeLinecap="round" />
      <path d="M322 350 358 54M362 350 398 54" stroke="#e0b53a" strokeWidth="5" strokeLinecap="round" />
      {rungs.map((rung) => {
        const y = 322 - rung * 38
        const lean = ((350 - y) / 296) * 36

        return <path key={rung} d={`M${322 + lean} ${y}h40`} stroke="#e0b53a" strokeWidth="4" />
      })}

      {[
        [18, 312, 64, 38],
        [25, 284, 50, 28],
        [32, 262, 36, 22],
      ].map(([x, y, w, h]) => (
        <g key={y}>
          <rect x={x} y={y} width={w} height={h} fill={PINK} stroke="#d88f96" strokeWidth="1" />
          <rect x={x + w / 2 - 2} y={y} width="4" height={h} fill={BLUE} />
          <rect x={x} y={y + h / 2 - 2} width={w} height="4" fill={BLUE} />
        </g>
      ))}
      <path d="M50 262c-12-14-18 0 0 0c18 0 12-14 0 0" fill="none" stroke={BLUE} strokeWidth="3" />
    </svg>
  )
}
