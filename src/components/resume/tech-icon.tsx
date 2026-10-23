import {
  siApple,
  siClaude,
  siDigitalocean,
  siDjango,
  siDocker,
  siElectron,
  siExpress,
  siFigma,
  siGhostty,
  siGin,
  siGo,
  siHono,
  siMacos,
  siMysql,
  siNextdotjs,
  siObsidian,
  siPostgresql,
  siPostman,
  siPython,
  siRedis,
  siSolid,
  siSvelte,
  siSwift,
  siTypescript,
  siXcode,
  siZedindustries,
  siZod,
} from 'simple-icons'
import type { ReactNode } from 'react'

// Brand marks from Simple Icons, as the reference sets its tools; anything without a mark of its own gets a plain
// Lucide line icon for what it is.
const BRANDS: Record<string, { path: string }> = {
  TypeScript: siTypescript,
  Swift: siSwift,
  Python: siPython,
  Golang: siGo,
  Obsidian: siObsidian,
  Postman: siPostman,
  Xcode: siXcode,
  Figma: siFigma,
  'Next.js': siNextdotjs,
  Django: siDjango,
  'Express.js': siExpress,
  'Hono.js': siHono,
  Gin: siGin,
  SvelteKit: siSvelte,
  SolidStart: siSolid,
  PostgreSQL: siPostgresql,
  MySQL: siMysql,
  'Digital Ocean Droplet': siDigitalocean,
  Zod: siZod,
  macOS: siMacos,
  Redis: siRedis,
  Docker: siDocker,
  'Claude Code': siClaude,
  Zed: siZedindustries,
  Ghostty: siGhostty,
  Electron: siElectron,
  AppKit: siApple,
  SwiftUI: siSwift,
}

const LINES: Record<string, ReactNode> = {
  code: <path d="m16 18 6-6-6-6M8 6l-6 6 6 6" />,
  database: (
    <>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5v14a9 3 0 0 0 18 0V5M3 12a9 3 0 0 0 18 0" />
    </>
  ),
  box: <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16ZM3.3 7l8.7 5 8.7-5M12 22V12" />,
  dot: (
    <>
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="1" />
    </>
  ),
  drive: <path d="M22 12H2M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11zM6 16h.01M10 16h.01" />,
  server: (
    <>
      <rect width="20" height="8" x="2" y="2" rx="2" />
      <rect width="20" height="8" x="2" y="14" rx="2" />
      <path d="M6 6h.01M6 18h.01" />
    </>
  ),
  function: (
    <>
      <rect width="18" height="18" x="3" y="3" rx="2" />
      <path d="M9 17c2 0 2.8-1 2.8-2.8V10c0-2 1-3.3 3.2-3M9 11.2h5.7" />
    </>
  ),
  sail: <path d="M22 18H2a4 4 0 0 0 4 4h12a4 4 0 0 0 4-4ZM21 14 10 2 3 14ZM10 2v16" />,
  cloud: <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />,
  palette: (
    <>
      <circle cx="13.5" cy="6.5" r=".5" />
      <circle cx="17.5" cy="10.5" r=".5" />
      <circle cx="8.5" cy="7.5" r=".5" />
      <circle cx="6.5" cy="12.5" r=".5" />
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.65-.75 1.65-1.69 0-.44-.18-.84-.44-1.13-.29-.29-.44-.65-.44-1.13a1.64 1.64 0 0 1 1.67-1.67h2c3.05 0 5.55-2.5 5.55-5.55C21.97 6.01 17.46 2 12 2z" />
    </>
  ),
  key: (
    <>
      <path d="M2.59 17.41A2 2 0 0 0 2 18.83V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.17a2 2 0 0 0 1.42-.59l.81-.81a6.5 6.5 0 1 0-4-4z" />
      <circle cx="16.5" cy="7.5" r=".5" />
    </>
  ),
  type: <path d="M4 7V4h16v3M9 20h6M12 4v16" />,
  zap: <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" />,
  presentation: <path d="M2 3h20M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3M7 21l5-5 5 5" />,
  mic: (
    <>
      <path d="M12 19v3M19 10v2a7 7 0 0 1-14 0v-2" />
      <rect x="9" y="2" width="6" height="13" rx="3" />
    </>
  ),
  book: <path d="M12 7v14M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z" />,
  shuffle: <path d="m18 14 4 4-4 4M18 2l4 4-4 4M2 18h1.97a4 4 0 0 0 3.3-1.7l5.45-7.6a4 4 0 0 1 3.3-1.7H22M2 6h1.97a4 4 0 0 1 3.6 2.2M22 18h-6.04a4 4 0 0 1-3.3-1.8l-.36-.45" />,
  monitor: (
    <>
      <rect width="20" height="14" x="2" y="3" rx="2" />
      <path d="M8 21h8M12 17v4" />
    </>
  ),
  file: <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7ZM14 2v4a2 2 0 0 0 2 2h4M16 13H8M16 17H8M10 9H8" />,
  buoy: (
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="m4.93 4.93 4.24 4.24M14.83 9.17l4.24-4.24M14.83 14.83l4.24 4.24M9.17 14.83l-4.24 4.24" />
      <circle cx="12" cy="12" r="4" />
    </>
  ),
  truck: (
    <>
      <path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2M15 18H9M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.62l-3.48-4.35A1 1 0 0 0 17.52 8H14" />
      <circle cx="17" cy="18" r="2" />
      <circle cx="7" cy="18" r="2" />
    </>
  ),
}

const GENERIC: Record<string, string> = {
  PopSQL: 'database',
  'VS Code': 'code',
  Spline: 'box',
  OrbStack: 'dot',
  RDS: 'database',
  S3: 'drive',
  EC2: 'server',
  Lambda: 'function',
  Lightsail: 'sail',
  'VPS servers': 'server',
  'Web design': 'palette',
  'serverless architectures': 'cloud',
  cryptography: 'key',
  typography: 'type',
  'low-latency back ends': 'zap',
  'T3 Code': 'code',
  Algorithms: 'book',
  'Network Security': 'book',
  'Computer Networks': 'book',
  'System Design and Database Optimization': 'book',
  'Product support': 'buoy',
  'product presentation': 'presentation',
  'public speaking': 'mic',
  'self-learning': 'book',
  adaptability: 'shuffle',
  Windows: 'monitor',
  EasyPost: 'truck',
  'pdf-lib': 'file',
}

/** The icon the reference sets beside a tool or skill: its brand mark if it has one, otherwise a line icon. */
export const TechIcon = ({ name, className = 'size-3.5 shrink-0 text-zinc-500 opacity-80' }: { name: string; className?: string }) => {
  const brand = BRANDS[name]
  if (brand) {
    return (
      <svg aria-hidden="true" role="img" viewBox="0 0 24 24" className={className} fill="currentColor">
        <path d={brand.path} />
      </svg>
    )
  }
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {LINES[GENERIC[name] ?? 'dot']}
    </svg>
  )
}
