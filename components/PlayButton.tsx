'use client'

import { openScreening } from "@/lib/screening"

function PlayGlyph() {
  return (
    <svg className="play-glyph" viewBox="0 0 10 11" aria-hidden="true">
      <path d="M0 0l10 5.5L0 11z" />
    </svg>
  )
}

// The header's Play control.
export default function PlayButton({ className = "bar-link" }: { className?: string }) {
  return (
    <button type="button" className={className} onClick={openScreening}>
      <PlayGlyph />
      Play
    </button>
  )
}

// The card that closes the stills grid: same window as a still, inverted.
export function PlayCard({ label, detail }: { label: string; detail: string }) {
  return (
    <button type="button" className="frame play-card" onClick={openScreening}>
      <svg viewBox="0 0 10 11" aria-hidden="true">
        <path d="M0 0l10 5.5L0 11z" />
      </svg>
      <b>{label}</b>
      <span>{detail}</span>
    </button>
  )
}
