/**
 * The poster's title, set as these films set theirs: bold Futura capitals in flat yellow, clean and centred
 * over the picture, the first words small and spaced out, the last one large.
 */
export function Masthead() {
  return (
    <header className="text-center font-futura font-bold text-[#f6cf43] uppercase">
      <h1>
        <span className="block text-[2.4cqw] leading-none tracking-[0.25em] [margin-right:-0.25em]">Where I&rsquo;ve</span>
        <span className="mt-[0.12em] block text-[12.5cqw] leading-[1.05] tracking-[0.04em] [margin-right:-0.04em]">Worked</span>
      </h1>
    </header>
  )
}
