'use client'

import { useCallback, useEffect, useRef, useState } from "react"
import Image from "next/image"
import { CARD_MS, END_MS, STILL_MS, onScreeningOpen } from "@/lib/screening"
import type { ScreeningPart } from "@/lib/types"

interface ScreeningProps {
  parts: ScreeningPart[]
  // What the end card says: the name.
  endTitle: string
}

// One beat of the picture. Each part is a card, then its still; the picture
// closes on an end card.
type Beat = { kind: "card" | "still"; part: number } | { kind: "end" }

function buildBeats(count: number): Beat[] {
  const beats: Beat[] = []
  for (let part = 0; part < count; part++) {
    beats.push({ kind: "card", part }, { kind: "still", part })
  }
  beats.push({ kind: "end" })
  return beats
}

const BEAT_MS = { card: CARD_MS, still: STILL_MS, end: END_MS }
// How much of a part's segment its card accounts for.
const CARD_SHARE = CARD_MS / (CARD_MS + STILL_MS)

// Play: the site run as a short picture. Every change is a cut; nothing fades
// or moves. With reduced motion set, it does not advance on its own.
export default function Screening({ parts, endTitle }: ScreeningProps) {
  const [open, setOpen] = useState(false)
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)
  // Lazy initial read (false on the server; the overlay is not in the first
  // render, so there is no hydration mismatch).
  const [reducedMotion, setReducedMotion] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  )
  const dialogRef = useRef<HTMLDivElement>(null)
  const beats = buildBeats(parts.length)
  const beat = beats[index]

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    const onChange = (e: MediaQueryListEvent) => setReducedMotion(e.matches)
    mq.addEventListener("change", onChange)
    return () => mq.removeEventListener("change", onChange)
  }, [])

  useEffect(
    () =>
      onScreeningOpen(() => {
        setIndex(0)
        setPaused(false)
        setOpen(true)
      }),
    [],
  )

  const stop = useCallback(() => setOpen(false), [])

  // Arrows cut to the card of the next or previous part.
  const cutTo = useCallback(
    (direction: 1 | -1) => {
      setIndex((current) => {
        const here = beats[current]
        const part = here.kind === "end" ? parts.length : here.part
        const target = Math.min(parts.length, Math.max(0, part + direction))
        return target * 2
      })
    },
    // beats is derived from parts.length
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [parts.length],
  )

  // The timer: hold the beat, then cut. The end card hands over to the credits.
  useEffect(() => {
    if (!open || paused || reducedMotion) return
    const timer = setTimeout(() => {
      if (beat.kind === "end") {
        stop()
        document.getElementById("about")?.scrollIntoView()
        return
      }
      setIndex((current) => current + 1)
    }, BEAT_MS[beat.kind])
    return () => clearTimeout(timer)
  }, [open, paused, reducedMotion, index, beat.kind, stop])

  // While open: lock scroll, take focus, listen for keys.
  useEffect(() => {
    if (!open) return
    const prevOverflow = document.body.style.overflow
    const prevFocus = document.activeElement as HTMLElement | null
    document.body.style.overflow = "hidden"
    dialogRef.current?.focus()

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") stop()
      else if (e.key === " ") { e.preventDefault(); setPaused((p) => !p) }
      else if (e.key === "ArrowRight") cutTo(1)
      else if (e.key === "ArrowLeft") cutTo(-1)
    }
    window.addEventListener("keydown", onKey)
    return () => {
      document.body.style.overflow = prevOverflow
      window.removeEventListener("keydown", onKey)
      prevFocus?.focus()
    }
  }, [open, stop, cutTo])

  if (!open || parts.length === 0) return null

  const part = beat.kind === "end" ? undefined : parts[beat.part]
  const field = part ? part.field : "teal"

  return (
    <div
      ref={dialogRef}
      tabIndex={-1}
      role="dialog"
      aria-modal="true"
      aria-label="Play"
      className={`screen-overlay f-${field} outline-none`}
    >
      <span className="keyline" aria-hidden="true" />

      {/* One segment per part; the current one fills as its card and still play */}
      <div className="reel" aria-hidden="true">
        {parts.map((_, i) => {
          const here = beat.kind === "end" ? parts.length : beat.part
          const state = i < here ? "done" : i === here ? "now" : "todo"
          const from = beat.kind === "still" ? CARD_SHARE : 0
          const to = beat.kind === "still" ? 1 : CARD_SHARE
          return (
            <span key={i} data-state={state}>
              {state === "now" && (
                <i
                  key={index}
                  style={{
                    "--from": from,
                    "--to": to,
                    transform: `scaleX(${reducedMotion ? to : from})`,
                    animation: reducedMotion
                      ? undefined
                      : `reel-fill ${BEAT_MS[beat.kind]}ms linear forwards`,
                    animationPlayState: paused ? "paused" : "running",
                  } as React.CSSProperties}
                />
              )}
            </span>
          )
        })}
      </div>

      <div aria-live="polite" className="contents">
        {beat.kind === "end" && (
          <>
            <p className="label">The end</p>
            <p className="screen-title">{endTitle}</p>
          </>
        )}
        {beat.kind === "card" && part && (
          <>
            <p className="label">Part {beat.part + 1} of {parts.length}</p>
            <p className="screen-title">{part.title}</p>
          </>
        )}
        {beat.kind === "still" && part && (
          <figure className="frame">
            <Image
              src={part.src}
              alt={part.alt}
              fill
              sizes="90vw"
              loading="eager"
              style={part.focus ? { objectPosition: part.focus } : undefined}
            />
            {part.note && <figcaption className="sub">{part.note}</figcaption>}
          </figure>
        )}
      </div>

      <div className="screen-controls">
        <button type="button" className="text-button" onClick={() => cutTo(-1)}>Previous</button>
        {!reducedMotion && (
          <button type="button" className="text-button" onClick={() => setPaused((p) => !p)}>
            {paused ? "Resume" : "Pause"}
          </button>
        )}
        <button type="button" className="text-button" onClick={() => cutTo(1)}>Next</button>
        <button type="button" className="text-button" onClick={stop}>Stop</button>
      </div>

      {/* Fetch the next still while its card is on screen */}
      {beat.kind === "card" && part && (
        <div className="fixed inset-0 opacity-0 pointer-events-none -z-10" aria-hidden="true">
          <Image src={part.src} alt="" fill sizes="90vw" loading="eager" />
        </div>
      )}
    </div>
  )
}
