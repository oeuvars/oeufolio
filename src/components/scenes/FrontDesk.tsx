import type { Signage } from '../../types'
import { Lettering } from './Lettering'
import { Mirror } from './Mirror'

const WALL = '#c4532a'
const WALL_DARK = '#a3401f'
const WALL_LINE = '#d96e3e'
const WOOD = '#6e2a18'
const HOLE = '#32130b'
const CREAM = '#fbf0d9'
const BRASS = '#d9a52b'
const PURPLE = '#5a3566'
const PURPLE_LINE = '#7d5490'
const MUSTARD = '#e0b53a'
const GREEN = '#2e7d6b'
const PINK = '#f3b9ae'
const BLUE = '#3f73a8'
const COCOA = '#3b1f1a'

const rows = [0, 1, 2, 3]
const columns = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

/**
 * The front desk of a lobby with nobody at it: a lit sign, a rack of pigeonholes with the post and the keys
 * in them, and a bell. The sign is the lightbox over the rack.
 */
export function FrontDesk({ sign }: Signage) {
  return (
    <svg viewBox="0 0 1200 500" preserveAspectRatio="xMidYMax slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="1200" height="500" fill={WALL} />
      <rect width="1200" height="46" fill={WALL_DARK} />
      <rect y="46" width="1200" height="3" fill={BRASS} />

      <Mirror>
        {/* A lift, and the dial that says which floor it is on. */}
        <path d="M100 104a40 40 0 0 1 80 0Z" fill={CREAM} stroke={BRASS} strokeWidth="3" />
        <path d="M140 102 122 78" stroke={COCOA} strokeWidth="2.5" strokeLinecap="round" />
        <rect x="60" y="112" width="160" height="388" fill={WALL_DARK} />
        <rect x="72" y="124" width="66" height="376" fill="#b84a25" />
        <rect x="142" y="124" width="66" height="376" fill="#b84a25" />
        <rect x="84" y="140" width="42" height="150" fill="none" stroke={WALL_LINE} strokeWidth="2" />
        <rect x="154" y="140" width="42" height="150" fill="none" stroke={WALL_LINE} strokeWidth="2" />
        <rect x="139" y="124" width="2" height="376" fill={BRASS} />

        <rect x="252" y="80" width="96" height="250" fill="none" stroke={WALL_LINE} strokeWidth="2" />
        <circle cx="300" cy="204" r="36" fill={CREAM} opacity="0.16" />
        <rect x="297" y="214" width="6" height="30" fill={BRASS} />
        <rect x="288" y="242" width="24" height="5" fill={BRASS} />
        <circle cx="300" cy="204" r="14" fill={CREAM} />
        <path d="M430 49V92" stroke={COCOA} strokeWidth="2" />
      </Mirror>

      <rect x="390" y="92" width="420" height="48" fill={CREAM} stroke={COCOA} strokeWidth="3" />
      <Lettering x={600} y={126} text={sign} width={380} max={28} tracking={0.3} fill={COCOA} />

      <rect x="380" y="152" width="440" height="10" fill="#8a3a22" />
      <rect x="388" y="162" width="424" height="170" fill={WOOD} />
      {rows.map((row) =>
        columns.map((column) => {
          const x = 407.6 + column * 39.2
          const y = 172 + row * 39

          return (
            <g key={`${row}-${column}`}>
              <rect x={x} y={y} width="32" height="30" fill={HOLE} />
              {(row * 3 + column * 5) % 4 === 0 && (
                <path d={`M${x + 5} ${y + 12}h22v18h-22Zm0 0 11 9 11-9`} fill={CREAM} stroke="#c9b48a" strokeWidth="1" />
              )}
              {(row + column * 2) % 5 === 1 && (
                <>
                  <path d={`M${x + 16} ${y}v10`} stroke={BRASS} strokeWidth="1.5" />
                  <circle cx={x + 16} cy={y + 15} r="5" fill="none" stroke={BRASS} strokeWidth="2.5" />
                </>
              )}
            </g>
          )
        }),
      )}

      <rect x="244" y="338" width="712" height="16" fill={MUSTARD} />
      <rect x="252" y="354" width="696" height="5" fill="#a9861f" />
      <rect x="260" y="359" width="680" height="141" fill={PURPLE} />
      <Mirror>
        <rect x="282" y="378" width="160" height="140" fill="none" stroke={PURPLE_LINE} strokeWidth="2.5" />
        <rect x="294" y="390" width="136" height="140" fill="none" stroke={PURPLE_LINE} strokeWidth="1.5" />

        <path d="M300 300 276 338H384L360 300Z" fill={CREAM} opacity="0.14" />
        <rect x="316" y="332" width="28" height="6" fill={BRASS} />
        <rect x="328" y="296" width="4" height="36" fill={BRASS} />
        <rect x="300" y="282" width="60" height="18" rx="9" fill={GREEN} />
      </Mirror>
      <rect x="470" y="378" width="260" height="140" fill="none" stroke={PURPLE_LINE} strokeWidth="2.5" />
      <path d="M600 400l9 18 20 3-14 14 3 20-18-9-18 9 3-20-14-14 20-3Z" fill={BRASS} />

      {/* The bell, a stack of cake boxes, and the register. */}
      <rect x="572" y="333" width="56" height="5" fill="#a87b16" />
      <path d="M580 333a20 20 0 0 1 40 0Z" fill={BRASS} />
      <circle cx="600" cy="311" r="4" fill={BRASS} />
      {[
        [452, 316, 46, 22],
        [458, 298, 34, 18],
        [464, 283, 22, 15],
      ].map(([x, y, w, h]) => (
        <g key={y}>
          <rect x={x} y={y} width={w} height={h} fill={PINK} stroke="#d88f86" strokeWidth="1" />
          <rect x={x + w / 2 - 1.5} y={y} width="3" height={h} fill={BLUE} />
        </g>
      ))}
      <path d="M475 283c-10-12-16 0-0 0c16 0 10-12 0 0" fill="none" stroke={BLUE} strokeWidth="2.5" />
      <path d="M690 338V330H748V338Z" fill={CREAM} stroke="#c9b48a" strokeWidth="1" />
      <path d="M719 330V338" stroke="#c9b48a" strokeWidth="1" />
      <path d="M752 334 778 322" stroke={COCOA} strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}
