type MastheadProps = {
  presenter: string
}

/**
 * The poster's title: yellow capitals in Geist Mono, spaced wide and centred over the picture, the first
 * words small and the last one large. Under them is whose picture it is, as these films credit their
 * director: in a formal script, the words small and the name larger under them. It is printed, not
 * set: the ink has bled a little at its edges and has not taken everywhere (the filters are in SiteShell).
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
      <p className="mt-[0.6cqw] font-script normal-case [filter:url(#print-fine)]">
        <span className="block text-[1.9cqw] leading-[1.3]">A picture by</span>
        <span className="block text-[3.9cqw] leading-[1.15]">{presenter}</span>
      </p>
    </header>
  )
}
