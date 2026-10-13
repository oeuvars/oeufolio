type MastheadProps = {
  presenter: string
}

/**
 * The poster's title: yellow capitals in Geist Mono, spaced wide and centred over the picture, the first
 * words small and the last one large, and whose picture it is under them in Instrument Serif's italic. It is printed, not set: the ink
 * has bled a little at its edges and has not taken everywhere (the filters are in SiteShell).
 */
export function Masthead({ presenter }: MastheadProps) {
  return (
    <header className="text-center font-geist text-[#f6cf43] uppercase">
      <h1 className="font-extrabold">
        <span className="block text-[2.5cqw] leading-none tracking-[0.5em] [margin-right:-0.5em] [filter:url(#print-fine)]">
          Where I&rsquo;ve
        </span>
        <span className="mt-[0.1em] block text-[13cqw] leading-[1.05] tracking-[0.06em] [margin-right:-0.06em] [filter:url(#print)]">Worked</span>
      </h1>
      <p className="font-instrument text-[3cqw] leading-none tracking-[0.02em] normal-case italic [filter:url(#print-fine)]">
        A picture by {presenter}
      </p>
    </header>
  )
}
