import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs: ClassValue[]) => {
  return twMerge(clsx(inputs))
}

/**
 * Where a strip shows on the window. A strip is laid as wide as it ever opens and slid so its edge lies where it should
 * (SiteShell's Strip), so its own box runs on under the strips before it: its [data-strip-box] is only the part that
 * shows, the box the strip would have if it were laid only that wide.
 */
export const stripRect = (strip: HTMLElement) =>
  (strip.querySelector<HTMLElement>(':scope > [data-strip-box]') ?? strip).getBoundingClientRect()
