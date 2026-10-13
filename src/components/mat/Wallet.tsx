import { useEffect, useRef, useState } from 'react'

import { PROP, RENDER } from './classes'

// The open render is one picture of both halves, 14.8 by 36 em with a 2 em bleed, and the fold runs across its
// middle. Two elements each show one half of it, so the upper half can turn about the fold on its own.
const HALF =
  'pointer-events-none absolute -inset-x-[2em] bg-[url(/objects/mat/wallet-open.avif)] bg-size-[18.8em_40em] bg-no-repeat'
// A cover turning about the fold, seen from straight above, only gets shorter. First one face of it stands up
// on the fold, gathering speed, and then the other face lies down, slowing, so the two moves read as one.
const TURN = 'transition-[scale,filter] motion-reduce:transition-none'
const STANDS = 'delay-0 duration-150 ease-in'
const LIES = 'delay-150 duration-200 ease-out'
const OPEN_STANDS = 'group-aria-expanded/wallet:delay-0 group-aria-expanded/wallet:duration-150 group-aria-expanded/wallet:ease-in'
const OPEN_LIES = 'group-aria-expanded/wallet:delay-150 group-aria-expanded/wallet:duration-200 group-aria-expanded/wallet:ease-out'
// How long the whole turn takes, and how far a pointer may travel in a press that still counts as a click.
const TURN_MS = 350
const SLOP = 5

/**
 * A black leather billfold with the fold at the top. A click unfolds it upward: the half underneath stays
 * where it lay and the cover swings up above it, with a photograph behind the window. Its box is the closed
 * wallet's, so the open one reaches 18 em out of the top of it.
 */
export function Wallet() {
  const [open, setOpen] = useState(false)
  // It stays above its neighbours until it has finished closing.
  const [raised, setRaised] = useState(false)
  const root = useRef<HTMLButtonElement>(null)
  const lowering = useRef(0)
  const press = useRef<{ x: number; y: number } | null>(null)
  const travel = useRef(0)

  useEffect(() => () => window.clearTimeout(lowering.current), [])

  const move = (event: React.PointerEvent) => {
    // Only a pointer the mat is dragging with can carry the wallet. A finger scrolls the page instead.
    if (!press.current || !root.current?.dataset.held) return
    travel.current += Math.abs(event.clientX - press.current.x) + Math.abs(event.clientY - press.current.y)
    press.current = { x: event.clientX, y: event.clientY }
  }
  const release = () => {
    press.current = null
  }
  const toggle = (event: React.MouseEvent) => {
    // The mat drags objects by the same press. A press that carried the wallet somewhere is not a click.
    // A key press has no pointer, so it always counts.
    if (event.detail !== 0 && travel.current >= SLOP) return
    const next = !open
    setOpen(next)
    window.clearTimeout(lowering.current)
    if (next) setRaised(true)
    else lowering.current = window.setTimeout(() => setRaised(false), TURN_MS)
  }

  return (
    <button
      ref={root}
      type="button"
      data-prop="wallet"
      data-raised={raised}
      aria-label="Wallet"
      aria-expanded={open}
      className={`${PROP} group/wallet z-1 h-[18em] w-[14.8em] [--bleed:1] [--tall:0.8] aria-expanded:[--tall:0.45] data-[raised=true]:z-900!`}
      onClick={toggle}
      onPointerDown={(event) => {
        press.current = { x: event.clientX, y: event.clientY }
        travel.current = 0
      }}
      onPointerMove={move}
      onPointerUp={release}
      onPointerCancel={release}
    >
      {/* The half that stays. It shows a pixel past the fold, so no seam opens between it and the cover. */}
      <i
        aria-hidden
        className={`${HALF} -top-px h-[calc(20em+1px)] bg-bottom opacity-0 transition-opacity delay-250 duration-100 group-aria-expanded/wallet:opacity-100 group-aria-expanded/wallet:delay-0 motion-reduce:transition-none`}
      />
      {/* The inside of the cover, swinging up from the fold. It is in its own shade until it lies back. */}
      <i
        aria-hidden
        className={`${HALF} ${TURN} ${STANDS} ${OPEN_LIES} bottom-full h-[20em] origin-bottom scale-y-0 bg-top brightness-50 group-aria-expanded/wallet:scale-y-100 group-aria-expanded/wallet:brightness-100`}
      />
      {/* The closed wallet, whose cover lifts toward the fold along its top edge. */}
      <i
        aria-hidden
        className={`${RENDER} ${TURN} ${LIES} ${OPEN_STANDS} pointer-events-none absolute -inset-[1em] origin-[50%_1em] bg-[url(/objects/mat/wallet.avif)] group-aria-expanded/wallet:scale-y-0 group-aria-expanded/wallet:brightness-50`}
      />
      {/* Open, it can be pressed anywhere on the half that has swung up as well. */}
      <span className="absolute inset-x-0 bottom-full hidden h-[18em] group-aria-expanded/wallet:block" />
    </button>
  )
}
