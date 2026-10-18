import type { CSSProperties } from 'react'

// The résumé page's two themes as variables, so one set of classes serves both. --l0 to --l4 are the five shades of
// the GitHub activity grid, from no contributions to the most.
export const LIGHT = {
  '--page': '#ffffff',
  '--ink': '#18181b',
  '--body': '#52525b',
  '--muted': '#71717a',
  '--faint': '#a1a1aa',
  '--rule': '#a1a1aa',
  '--line': '#e4e4e7',
  '--chip': '#fafafa',
  '--chip-line': 'rgb(0 0 0 / 0.3)',
  '--hover': '#f4f4f5',
  '--button': '#18181b',
  '--button-ink': '#fafafa',
  '--l0': '#f4f4f5',
  '--l1': '#d4d4d8',
  '--l2': '#a1a1aa',
  '--l3': '#52525b',
  '--l4': '#18181b',
} as CSSProperties

export const DARK = {
  '--page': '#000000',
  '--ink': '#f4f4f5',
  '--body': '#d4d4d8',
  '--muted': '#a1a1aa',
  '--faint': '#52525b',
  '--rule': '#52525b',
  '--line': '#27272a',
  '--chip': '#0a0a0a',
  '--chip-line': 'rgb(255 255 255 / 0.25)',
  '--hover': '#121214',
  '--button': '#fafafa',
  '--button-ink': '#18181b',
  '--l0': '#18181b',
  '--l1': '#3f3f46',
  '--l2': '#71717a',
  '--l3': '#d4d4d8',
  '--l4': '#fafafa',
} as CSSProperties

export const FOCUS = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--ink)'
export const MONO = "font-['Geist_Mono_Variable',ui-monospace,monospace]"
export const LABEL = `${MONO} text-[10px] font-medium tracking-wider text-(--faint) uppercase`
export const CHIP = `flex items-center gap-1.5 rounded-[4px] border border-(--line) bg-(--chip) px-3 py-1.5 text-[12px] font-medium text-(--body) transition-colors hover:bg-(--hover) hover:text-(--ink) ${FOCUS}`
export const STAMP = `flex items-center gap-1.5 rounded-[4px] border border-(--line) bg-(--chip) px-3 py-1.5 ${MONO} text-[10px] tracking-[0.12em] text-(--muted) uppercase transition-colors hover:bg-(--hover) hover:text-(--ink) ${FOCUS}`
export const PILL = 'flex w-fit shrink-0 items-center gap-1.5 rounded-full border border-(--line) bg-(--page) px-2 py-0.5 text-[11px] font-medium text-(--muted)'
export const CARD = 'rounded-lg border border-(--line) bg-(--chip)'

// Dotted rules as the reference draws them: a one-pixel dot every four pixels, sparser than CSS's own dotted border.
export const DOTS_X = 'bg-[linear-gradient(to_right,var(--rule)_1px,transparent_1px)] bg-[length:4px_1px] bg-repeat-x'
export const DOTS_Y = 'bg-[linear-gradient(to_bottom,var(--rule)_1px,transparent_1px)] bg-[length:1px_4px] bg-repeat-y'
export const DOT = 'relative before:absolute before:top-[0.75em] before:-left-3 before:size-[3px] before:rounded-full before:bg-current'
