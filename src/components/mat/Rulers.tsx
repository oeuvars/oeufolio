type RulersProps = {
  /** The mat is cut off at its right edge, as on a folded strip, and has no ruler there. */
  cut?: boolean
}

const MARKS = Array.from({ length: 40 }, (_, i) => i * 5)
const RULER =
  'pointer-events-none absolute z-1 flex overflow-hidden bg-[color-mix(in_srgb,var(--color-mat)_82%,var(--ink))] font-mono text-[0.56rem]/none font-medium text-ink/80'

/** The mat's rulers: one along each edge, with a plain square where two meet. */
export function Rulers({ cut }: RulersProps) {
  const end = cut ? 'right-0' : 'right-[22px]'
  const corners = cut ? ['top-0 left-0', 'bottom-0 left-0'] : ['top-0 left-0', 'top-0 right-0', 'bottom-0 left-0', 'right-0 bottom-0']

  return (
    <>
      <div aria-hidden className={`${RULER} ${end} top-0 left-[22px] h-[22px] bg-ticks-x bg-size-[24px_8px] bg-position-[0_14px] bg-repeat-x`}>
        {MARKS.map((mark) => (
          <span key={mark} className="w-[120px] flex-none border-l border-ink/60 pt-1 pl-1">
            {mark}
          </span>
        ))}
      </div>
      <div aria-hidden className={`${RULER} ${end} bottom-0 left-[22px] h-[22px] bg-ticks-x bg-size-[24px_8px] bg-position-[0_0] bg-repeat-x`}>
        {MARKS.map((mark) => (
          <span key={mark} className="flex w-[120px] flex-none items-end border-l border-ink/60 pb-1 pl-1">
            {mark}
          </span>
        ))}
      </div>
      <div aria-hidden className={`${RULER} top-[22px] bottom-[22px] left-0 w-[22px] flex-col bg-ticks-y bg-size-[8px_24px] bg-position-[14px_0] bg-repeat-y`}>
        {MARKS.map((mark) => (
          <span key={mark} className="h-[120px] flex-none border-t border-ink/60 pt-1 pl-[3px]">
            {mark}
          </span>
        ))}
      </div>
      {!cut && (
        <div aria-hidden className={`${RULER} top-[22px] right-0 bottom-[22px] w-[22px] flex-col bg-ticks-y bg-size-[8px_24px] bg-position-[0_0] bg-repeat-y`}>
          {MARKS.map((mark) => (
            <span key={mark} className="h-[120px] flex-none border-t border-ink/60 pt-1 pr-[3px] text-right">
              {mark}
            </span>
          ))}
        </div>
      )}
      {corners.map((corner) => (
        <i key={corner} aria-hidden className={`${RULER} ${corner} size-[22px]`} />
      ))}
    </>
  )
}
