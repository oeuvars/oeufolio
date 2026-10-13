type MastheadProps = {
  presenter: string
}

/**
 * The poster's title, set as these films set theirs: yellow capitals in the geometric face, spaced wide
 * and centred over the picture, the first words small and the last one large, and whose picture it is
 * under them.
 */
export function Masthead({ presenter }: MastheadProps) {
  return (
    <header className="text-center text-[#f6cf43] uppercase [text-shadow:0_0.06em_0.18em_rgb(10_14_30/0.55)]">
      <h1 className="font-bold">
        <span className="block text-[2.6cqw] leading-none tracking-[0.55em] [margin-right:-0.55em]">Where I&rsquo;ve</span>
        <span className="mt-[0.08em] block text-[11.5cqw] leading-[1.05] tracking-[0.16em] [margin-right:-0.16em]">Worked</span>
      </h1>
      <p className="text-[1.55cqw] leading-none font-semibold tracking-[0.5em] [margin-right:-0.5em]">A picture by {presenter}</p>
    </header>
  )
}
