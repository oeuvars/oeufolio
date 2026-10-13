import type { Signage } from '../../types'
import { Lettering } from './Lettering'

const WALL = '#2f8189'
const DADO = '#276d75'
const FLOOR = '#7a4a2e'
const CREAM = '#fbf0d9'
const BRASS = '#d9a52b'
const COCOA = '#3b1f1a'
const WOOD = '#6e2a18'
const OAK = '#c9862a'
const spines = ['#b3291b', '#f2b632', '#fbf0d9', '#3f73a8', '#f3a9b4', '#2e7d6b']

const shelves = [0, 1, 2, 3]
const books = [0, 1, 2, 3, 4, 5, 6, 7]
const drawers = [0, 1, 2, 3]

/**
 * A writer's office: a typewriter on an oak desk, the books, a filing cabinet with a wireless on it, and
 * the mountains in the window. The sign is the board over the window.
 */
export function Office({ sign }: Signage) {
  return (
    <svg viewBox="0 0 480 400" preserveAspectRatio="xMidYMax slice" aria-hidden className="absolute inset-0 size-full">
      <rect width="480" height="400" fill={WALL} />
      <rect y="262" width="480" height="88" fill={DADO} />
      <rect y="258" width="480" height="4" fill="#45a0a8" />
      <rect y="350" width="480" height="50" fill={FLOOR} />
      <path d="M0 366H480M0 383H480" stroke="#63391f" strokeWidth="1.5" />
      <ellipse cx="240" cy="374" rx="150" ry="13" fill="#b3291b" />

      <rect x="110" y="26" width="260" height="34" fill={CREAM} stroke={BRASS} strokeWidth="3" />
      <Lettering x={240} y={50} text={sign} width={236} max={18} tracking={0.22} fill={COCOA} />

      <path d="M150 80H330" stroke={BRASS} strokeWidth="4" strokeLinecap="round" />
      <rect x="172" y="84" width="136" height="126" fill={CREAM} />
      <rect x="180" y="92" width="120" height="110" fill="#c9e0d6" />
      <path d="M180 202 210 152 232 174 262 126 300 184V202Z" fill="#a79fb6" />
      <path d="M262 126l-12 19 8-4 6 7 7-8 5 4Z" fill="#f6efe2" />
      <path d="M240 92V202M180 147H300" stroke={CREAM} strokeWidth="5" />
      <path d="M158 82h22v118c-12 6-18 14-22 26Z" fill="#e0a12e" />
      <path d="M322 82h-22v118c12 6 18 14 22 26Z" fill="#e0a12e" />

      <rect x="22" y="90" width="104" height="260" fill={WOOD} />
      {shelves.map((shelf) => (
        <g key={shelf}>
          <rect x="30" y={98 + shelf * 62} width="88" height="54" fill="#32130b" />
          {books.map((book) => {
            const height = 30 + ((shelf * 5 + book * 7) % 4) * 6

            return (
              <rect
                key={book}
                x={32 + book * 10.6}
                y={152 + shelf * 62 - height}
                width="9"
                height={height}
                fill={spines[(shelf + book * 3) % spines.length]}
              />
            )
          })}
        </g>
      ))}

      <rect x="360" y="168" width="96" height="182" fill="#8fa6a2" stroke="#5f7672" strokeWidth="2" />
      {drawers.map((drawer) => (
        <g key={drawer}>
          <rect x="368" y={176 + drawer * 43} width="80" height="36" fill="#a3b8b4" stroke="#5f7672" strokeWidth="1.5" />
          <rect x="400" y={183 + drawer * 43} width="16" height="8" fill={CREAM} />
          <rect x="398" y={197 + drawer * 43} width="20" height="5" rx="2.5" fill={BRASS} />
        </g>
      ))}
      <circle cx="380" cy="130" r="13" fill="#5f8a5e" />
      <circle cx="396" cy="122" r="15" fill="#4f7a50" />
      <circle cx="390" cy="140" r="11" fill="#6f9a6a" />
      <path d="M376 148h28l-4 20h-20Z" fill="#c4532a" />
      <rect x="414" y="146" width="36" height="22" rx="4" fill="#2e7d6b" />
      <circle cx="441" cy="157" r="5" fill={CREAM} />
      <path d="M419 152h14M419 157h14M419 162h14" stroke={CREAM} strokeWidth="1.5" />

      <rect x="118" y="290" width="244" height="10" fill="#e0a12e" />
      <rect x="130" y="300" width="220" height="50" fill={OAK} />
      <rect x="212" y="300" width="56" height="50" fill="#63391f" />
      {[138, 276].map((x) =>
        [308, 328].map((y) => (
          <g key={`${x}-${y}`}>
            <rect x={x} y={y} width="66" height="16" fill="none" stroke="#a56a1c" strokeWidth="1.5" />
            <circle cx={x + 33} cy={y + 8} r="2.5" fill={BRASS} />
          </g>
        )),
      )}

      <rect x="224" y="232" width="32" height="30" fill={CREAM} />
      <path d="M229 240h22M229 246h22M229 252h14" stroke="#c9b48a" strokeWidth="1.5" />
      <rect x="206" y="258" width="68" height="7" rx="3.5" fill={COCOA} />
      <rect x="212" y="264" width="56" height="26" rx="5" fill="#3f73a8" />
      {[276, 283].map((y) =>
        [0, 1, 2, 3, 4, 5].map((key) => <circle key={`${y}-${key}`} cx={220 + key * 8} cy={y} r="2" fill={CREAM} />),
      )}
      <rect x="140" y="284" width="26" height="6" fill={BRASS} />
      <rect x="151" y="254" width="4" height="30" fill={BRASS} />
      <rect x="132" y="242" width="42" height="14" rx="7" fill="#2e7d6b" />
      <rect x="300" y="280" width="44" height="10" fill="#b3291b" />
      <rect x="304" y="271" width="38" height="9" fill="#f2b632" />
      <rect x="302" y="262" width="40" height="9" fill={CREAM} />
    </svg>
  )
}
