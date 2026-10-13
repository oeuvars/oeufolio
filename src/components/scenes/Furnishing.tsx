const BRASS = '#d9a52b'
const COCOA = '#3b1f1a'

type FurnishingProps = {
  /** Which piece: they are dealt out in order, and come round again. */
  index: number
}

/** One thing standing on the floor beside a notice: a palm in a pot, a standard lamp or a hat stand. */
export function Furnishing({ index }: FurnishingProps) {
  const piece = index % 3

  return (
    <svg viewBox="0 0 60 150" aria-hidden className="block h-auto w-full">
      {piece === 0 && (
        <>
          <path d="M30 108C22 78 8 62 2 58M30 108C30 70 30 48 30 34M30 108C38 78 52 62 58 58M30 108C24 88 14 84 6 86M30 108C36 88 46 84 54 86" fill="none" stroke="#3f7a4d" strokeWidth="5" strokeLinecap="round" />
          <path d="M16 108h28l-4 42H20Z" fill="#c4532a" />
          <rect x="14" y="104" width="32" height="8" fill="#a3401f" />
        </>
      )}
      {piece === 1 && (
        <>
          <path d="M12 44 20 8H40L48 44Z" fill="#f2b632" />
          <path d="M12 44H48" stroke={COCOA} strokeWidth="2" />
          <rect x="28.5" y="44" width="3" height="100" fill={BRASS} />
          <rect x="16" y="144" width="28" height="6" rx="3" fill={BRASS} />
        </>
      )}
      {piece === 2 && (
        <>
          <rect x="28.5" y="14" width="3" height="130" fill={COCOA} />
          <path d="M30 26C22 24 16 18 14 10M30 26C38 24 44 18 46 10M30 40C20 38 14 32 10 26M30 40C40 38 46 32 50 26" fill="none" stroke={COCOA} strokeWidth="3" strokeLinecap="round" />
          <path d="M4 14h20l-3-10H8Z" fill="#b3291b" />
          <rect x="1" y="13" width="26" height="3" rx="1.5" fill="#8a1f14" />
          <path d="M18 150 30 136 42 150" fill="none" stroke={COCOA} strokeWidth="3" strokeLinecap="round" />
        </>
      )}
    </svg>
  )
}
