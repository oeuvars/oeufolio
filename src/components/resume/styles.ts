import type { CSSProperties } from 'react'

// Class sets taken from parascodes.is-a.dev, which the résumé page copies: its zinc palette, its black/30 rules masked
// into one-pixel dots every six pixels, black/5 rings and its radii and shadows, in light and dark.

export const MONO = "font-['Geist_Mono_Variable',ui-monospace,monospace]"

/** A rule's dash: one pixel drawn in every six. */
export const DASH_X: CSSProperties = {
  maskImage: 'repeating-linear-gradient(to right, black 0, black 1px, transparent 1px, transparent 6px)',
  WebkitMaskImage: 'repeating-linear-gradient(to right, black 0, black 1px, transparent 1px, transparent 6px)',
}
export const DASH_Y: CSSProperties = {
  maskImage: 'repeating-linear-gradient(to bottom, black 0, black 1px, transparent 1px, transparent 6px)',
  WebkitMaskImage: 'repeating-linear-gradient(to bottom, black 0, black 1px, transparent 1px, transparent 6px)',
}

export const RULE = 'pointer-events-none absolute h-0 border-black/30 dark:border-white/[0.15]'
export const KNOT = 'pointer-events-none absolute z-20 size-[2px] bg-black/50 dark:bg-white/[0.25]'

/** The outline drawn five pixels outside a card or button, darkening on hover. */
export const RING =
  'pointer-events-none absolute -inset-[5px] rounded-[11px] border border-black/5 transition-colors duration-300 group-hover:border-black/10 dark:border-white/5 dark:group-hover:border-white/10'
export const CARD =
  'relative flex flex-col overflow-hidden rounded-[6px] border border-black/5 bg-zinc-50 shadow-sm shadow-black/5 dark:border-white/5 dark:bg-[#09090b] dark:shadow-lg dark:shadow-black/80'

export const CHIP =
  'rounded-[6px] border border-black/30 bg-zinc-100 px-2.5 py-1 text-[12px] font-medium text-zinc-600 dark:border-white/[0.15] dark:bg-[#0a0a0a] dark:text-zinc-400'
export const LABEL = `${MONO} text-[10px] font-medium tracking-wider text-zinc-400 uppercase dark:text-zinc-600`
export const STAMP = `group inline-flex items-center gap-2 rounded-[6px] border border-black/5 bg-zinc-50 px-3 py-1.5 ${MONO} text-[10px] tracking-[0.16em] text-zinc-400 uppercase transition-colors hover:text-zinc-700 dark:border-white/5 dark:bg-[#09090b] dark:text-zinc-600 dark:hover:text-zinc-300`
export const FOCUS = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-400'
