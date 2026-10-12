import { cn } from '@/lib/utils'

type FoilCornerProps = {
  className?: string
}

export function FoilCorner({ className }: FoilCornerProps) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 80 80"
      className={cn('pointer-events-none absolute h-[3.6em] w-[3.6em]', className)}
      fill="none"
    >
      <defs>
        <linearGradient id="foil-stroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#8a5b12" />
          <stop offset="0.35" stopColor="#f3d98a" />
          <stop offset="0.6" stopColor="#c8962e" />
          <stop offset="1" stopColor="#fff0b0" />
        </linearGradient>
      </defs>
      <path d="M4 76 V30 C4 14 14 4 30 4 H76" stroke="url(#foil-stroke)" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M12 76 V34 C12 20 20 12 34 12 H76" stroke="url(#foil-stroke)" strokeWidth="1" strokeLinecap="round" />
      <path
        d="M22 22 C22 30 30 32 34 28 C38 24 34 18 28 20 C24 21.5 24 26 27 26"
        stroke="url(#foil-stroke)"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
      <circle cx="40" cy="40" r="2.4" fill="url(#foil-stroke)" />
    </svg>
  )
}
