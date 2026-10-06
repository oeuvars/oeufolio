// Bridge between the Play controls (header, stills page) and the Screening
// overlay mounted by the header. Same pattern as lib/contactPrefill.ts.
// Client-only: do not import from Server Components.

const EVENT_NAME = "screening-open"

// How long each beat holds, in milliseconds: the part card, the still, the end card.
export const CARD_MS = 1600
export const STILL_MS = 5000
export const END_MS = 2400

export function openScreening(): void {
  window.dispatchEvent(new Event(EVENT_NAME))
}

export function onScreeningOpen(callback: () => void): () => void {
  window.addEventListener(EVENT_NAME, callback)
  return () => window.removeEventListener(EVENT_NAME, callback)
}

export function screeningSeconds(parts: number): number {
  return Math.round((parts * (CARD_MS + STILL_MS)) / 1000)
}
