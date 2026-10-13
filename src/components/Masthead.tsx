type MastheadProps = {
  presenter: string
  /** The page's number in the file. */
  issue: number
  parts: number
  works: number
}

const numerals = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
const count = (n: number) => numerals[n] ?? String(n)

/**
 * The poster's masthead, set as a magazine's is: the issue and what is in it at the corners, the first words
 * of the title small in a box, the last one in condensed capitals as wide as the sheet, and a line between
 * two rules to say whose picture it is.
 */
export function Masthead({ presenter, issue, parts, works }: MastheadProps) {
  return (
    <header className="text-cocoa">
      <p className="flex justify-between text-[0.66em] font-bold tracking-[0.22em] uppercase">
        <span>N° {String(issue).padStart(2, '0')}</span>
        <span>
          {count(parts)} parts, {count(works)} works
        </span>
      </p>
      <h1 className="mt-[1.4cqw] flex items-stretch gap-[2cqw] font-display font-black uppercase [font-stretch:62%] [filter:url(#print)]">
        <span className="flex flex-col justify-center border-[0.55cqw] border-cocoa px-[1.3cqw] text-[5.6cqw] leading-[0.92]">
          <span>Where</span>
          <span>I&rsquo;ve</span>
        </span>
        <span className="flex-1 text-[23.2cqw] leading-[0.74] tracking-[-0.012em] [text-shadow:0.03em_0.03em_0_var(--color-brick)]">Worked</span>
      </h1>
      <p className="mt-[2cqw] border-y-[0.4cqw] border-cocoa py-[0.9cqw] text-center text-[0.7em] font-bold tracking-[0.34em] uppercase">
        A picture by {presenter}
        <span aria-hidden className="mx-[0.8em]">★</span>
        in {count(parts)} parts
      </p>
    </header>
  )
}
