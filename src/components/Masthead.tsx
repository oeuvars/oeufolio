type MastheadProps = {
  presenter: string
  /** The page's number in the file. */
  issue: number
}

/**
 * The poster's masthead, set as a magazine's is: the first words of the title small in a box, the last one
 * in condensed capitals, and beside them, between two rules, the issue and whose picture it is. On a narrow
 * sheet the title takes the whole width and the rest goes under it.
 */
export function Masthead({ presenter, issue }: MastheadProps) {
  return (
    <header className="flex flex-col gap-[2cqw] text-cocoa @md/box:flex-row @md/box:items-stretch">
      <h1 className="flex items-stretch gap-[2cqw] font-display font-black uppercase [font-stretch:62%] [filter:url(#print)] @md/box:gap-[1.6cqw]">
        <span className="flex flex-col justify-center border-[0.55cqw] border-cocoa px-[1.3cqw] text-[5.6cqw] leading-[0.92] @md/box:border-[0.45cqw] @md/box:px-[1cqw] @md/box:text-[4cqw]">
          <span>Where</span>
          <span>I&rsquo;ve</span>
        </span>
        <span className="text-[23.2cqw] leading-[0.74] tracking-[-0.012em] [text-shadow:0.03em_0.03em_0_var(--color-brick)] @md/box:text-[16.5cqw]">
          Worked
        </span>
      </h1>
      <p className="flex flex-1 items-baseline justify-between gap-[1em] border-y-[0.4cqw] border-cocoa py-[0.8cqw] text-[0.64em] leading-[1.5] font-bold tracking-[0.26em] uppercase @md/box:flex-col @md/box:items-end @md/box:text-right">
        <span>N° {String(issue).padStart(2, '0')}</span>
        <span>
          A picture by <span className="@md/box:block">{presenter}</span>
        </span>
      </p>
    </header>
  )
}
