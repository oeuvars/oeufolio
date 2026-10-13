import { cn } from '../../lib/utils'
import type { Credit } from '../../types'
import { BAKED, KICKER, LIVE, PROP, SKIN } from './classes'
import { useKolkata } from './useKolkata'

type RowProps = {
  label: string
  /** A live entry is not in the render. */
  live?: boolean
  children: React.ReactNode
}

/** One line of the form: a label and, across from it, the entry. */
function Row({ label, live, children }: RowProps) {
  return (
    <div className="flex items-baseline justify-between gap-[0.5em] py-[0.3em]">
      <dt className="font-mono text-[0.56em]/[1.3] font-medium tracking-[0.12em] uppercase">{label}</dt>
      <dd className={cn('font-mono text-[0.72em]/[1.3] font-medium tabular-nums', live && `${LIVE} text-ink`)}>{children}</dd>
    </div>
  )
}

type IdCardProps = {
  particulars: Credit[]
}

/**
 * The particulars: a ledger form kept flat under a slab of glass. The form and its entries are in the
 * render, and are set here in the same places for readers. Only the clock is live.
 */
export function IdCard({ particulars }: IdCardProps) {
  const kolkata = useKolkata()

  return (
    <article
      data-prop="particulars"
      className={`${PROP} ${BAKED} z-2 h-[11.1875em] w-[20.625em] px-[1.1em] pt-[0.95em] [--bleed:1.9] [--k:1.15] [--tall:0.5] stacked:[--k:1]`}
    >
      <i aria-hidden className={`${SKIN} bg-[url(/objects/mat/form.avif)]`} />
      <header className={`${KICKER} flex justify-between gap-[1em] border-b-[1.5px] pb-[0.7em]`}>
        <span>The particulars</span>
        <span>Form A–1</span>
      </header>
      <dl className="mt-[0.45em]">
        {particulars.map((row) => (
          <Row key={row.label} label={row.label}>
            {row.value}
          </Row>
        ))}
        <Row label="Local time" live>
          {kolkata.time && `${kolkata.time} IST`}
        </Row>
      </dl>
    </article>
  )
}
