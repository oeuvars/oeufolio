import { useEffect, useRef } from 'react'

import { RENDER } from './classes'

type PendantLampProps = {
  lit: boolean
  onPull: () => void
}

// Every render overhangs the lamp's box by this many em, which lets the flex run off the top of the frame.
const BLEED = 0.5
const LAYER = `${RENDER} absolute inset-0`
// The base renders, dim in the dark room and lifted a little by the lamp's own light.
const DIMMED = 'brightness-[calc(0.3+0.25*var(--lit))]'
const GLOW = 'opacity-0 mix-blend-screen transition-opacity duration-300 data-[lit=true]:opacity-100'

// The lamp's set, in em from the top left of the lamp's box.
// The flex is fixed to a ceiling this far above the frame, and the lamp swings from there.
const CEILING = 8
// Where the chain leaves the lampholder, up inside the shade.
const HOOK = { x: 5.813, y: 6.774 }
// The lower edge of the shade's near lip. The chain is behind the shade above this line and in sight below it.
const LIP = { x: 4.5, y: 10.079, across: 2.795, rise: 0.355 }
const MOUTH = (() => {
  const points = [`0 ${LIP.y + BLEED}em`]
  for (let i = 0; i <= 24; i++) {
    const x = (i / 12 - 1) * LIP.across
    points.push(`${(LIP.x + x + BLEED).toFixed(3)}em ${(LIP.y - LIP.rise * Math.sqrt(LIP.across ** 2 - x ** 2) + BLEED).toFixed(3)}em`)
  }
  return `polygon(${points.join(', ')}, 12em ${LIP.y + BLEED}em, 12em 18em, 0 18em)`
})()

// Two pendulums and a spring. The lamp on its flex takes about 1.6 seconds a swing, as a lamp hung 65 cm
// below a ceiling does, and loses little each time. The chain is shorter, so it swings faster, and the lamp
// drags its hook about under it. The chain is drawn down against a spring in the switch.
const LAMP = { rate: (2 * Math.PI) / 1.62, loss: 0.06 }
const CHAIN = { rate: (2 * Math.PI) / 0.98, loss: 0.07, lever: 2.3 }
// A pull draws the chain down by reach em. It hangs right of the flex, so the pull also tips the lamp by lean.
// The hand draws it down without a bounce. Let go, the spring takes it back with one, and as the chain goes
// slack it is flicked sideways by kick. A hand on the chain also steadies the lamp, by steady.
const PULL = { reach: 0.5, lean: 0.06, rate: 42, loss: 0.42, hold: 150, kick: 0.5, steady: 0.6 }
const STEP = 1 / 240
// Below this many radians, and ten times it a second, nothing on screen moves by a pixel.
const STILL = 0.0004
const degrees = (angle: number) => `${((angle * 180) / Math.PI).toFixed(3)}deg`

/**
 * A pendant lamp hung over the top right of the mat, sized and placed by its holder: a terracotta shade, a
 * brass lampholder and chain, a clear bulb. The lamp and its chain are each two renders of one set. The first is in the studio's
 * light with the bulb off. The second holds only what the bulb adds and is laid over the first when the lamp
 * is lit. Pressing draws the chain down and tips the lamp. Letting go switches it, and both swing until they
 * settle.
 */
export function PendantLamp({ lit, onPull }: PendantLampProps) {
  const lamp = useRef<HTMLButtonElement>(null)
  const chain = useRef<HTMLSpanElement>(null)
  // The hand on the chain. The effect below puts the working pair here.
  const hand = useRef({ grip: () => {}, release: () => {} })

  useEffect(() => {
    const body = lamp.current
    const links = chain.current
    if (!body || !links || matchMedia('(prefers-reduced-motion: reduce)').matches) return
    // Angles are clockwise from hanging straight, in radians. The chain's is its own, not measured from the lamp.
    const state = { swing: 0, swingSpeed: 0, sway: 0, swaySpeed: 0, drawn: 0, drawnSpeed: 0 }
    let held = false
    let flick = false
    let heldAt = 0
    let letting = 0
    let frame = 0
    let last = 0
    let owed = 0

    const step = () => {
      const taut = Math.max(0, state.drawn) / PULL.reach
      const drawnPush = -(PULL.rate ** 2) * (state.drawn - (held ? PULL.reach : 0)) - 2 * (held ? 1 : PULL.loss) * PULL.rate * state.drawnSpeed
      state.drawnSpeed += drawnPush * STEP
      state.drawn += state.drawnSpeed * STEP
      if (flick && state.drawn < PULL.reach * 0.1) {
        flick = false
        state.swaySpeed += PULL.kick
      }
      const swingPush =
        -(LAMP.rate ** 2) * (state.swing - PULL.lean * taut) - 2 * (LAMP.loss + PULL.steady * taut) * LAMP.rate * state.swingSpeed
      state.swingSpeed += swingPush * STEP
      state.swing += state.swingSpeed * STEP
      // A chain under tension is held straight. Let go, it is free, and the lamp moving its hook sets it going.
      const swayPush =
        -(CHAIN.rate ** 2) * (1 + 9 * taut) * state.sway - 2 * (CHAIN.loss + 0.5 * taut) * CHAIN.rate * state.swaySpeed - CHAIN.lever * swingPush
      state.swaySpeed += swayPush * STEP
      state.sway += state.swaySpeed * STEP
    }
    const draw = () => {
      body.style.rotate = degrees(state.swing)
      links.style.translate = `0 ${state.drawn.toFixed(4)}em`
      links.style.rotate = degrees(state.sway - state.swing)
    }
    const tick = (now: number) => {
      owed += Math.min(0.05, Math.max(0, now - last) / 1000)
      last = now
      for (; owed >= STEP; owed -= STEP) step()
      const moving =
        [state.swing, state.sway, state.drawn].some((value) => Math.abs(value) > STILL) ||
        [state.swingSpeed, state.swaySpeed, state.drawnSpeed].some((value) => Math.abs(value) > STILL * 10)
      if (!held && !moving) {
        for (const key of Object.keys(state) as (keyof typeof state)[]) state[key] = 0
        frame = 0
        owed = 0
      } else frame = requestAnimationFrame(tick)
      draw()
    }
    const grip = () => {
      window.clearTimeout(letting)
      held = true
      heldAt = performance.now()
      if (!frame) {
        last = heldAt
        frame = requestAnimationFrame(tick)
      }
    }
    // A quick click is still a pull: the chain is held long enough to come down before it is let go.
    const release = () => {
      if (!held) return
      window.clearTimeout(letting)
      letting = window.setTimeout(
        () => {
          held = false
          flick = true
        },
        Math.max(0, PULL.hold - (performance.now() - heldAt)),
      )
    }
    hand.current = { grip, release }

    return () => {
      cancelAnimationFrame(frame)
      window.clearTimeout(letting)
    }
  }, [])

  const pull = (event: React.MouseEvent) => {
    onPull()
    // A key press has no pointer to hold the chain, so it gets a pull of its own.
    if (event.detail === 0) {
      hand.current.grip()
      hand.current.release()
    }
  }

  return (
    <button
      ref={lamp}
      type="button"
      aria-label="Lamp"
      aria-pressed={lit}
      data-lamp
      className="absolute top-0 left-0 isolate h-[13.6em] w-[9em] cursor-pointer touch-manipulation"
      style={{ transformOrigin: `50% ${-CEILING}em` }}
      onClick={pull}
      onPointerDown={(event) => event.button === 0 && hand.current.grip()}
      onPointerUp={() => hand.current.release()}
      onPointerLeave={() => hand.current.release()}
      onPointerCancel={() => hand.current.release()}
    >
      <span className="pointer-events-none absolute -inset-[0.5em]">
        <i className={`${LAYER} ${DIMMED} bg-[url(/objects/mat/lamp.avif)]`} />
        <i data-lit={lit} className={`${LAYER} ${GLOW} bg-[url(/objects/mat/lamp-glow.avif)]`} />
      </span>
      <span className="pointer-events-none absolute -inset-[0.5em]" style={{ clipPath: MOUTH }}>
        <span ref={chain} className="absolute inset-0" style={{ transformOrigin: `${HOOK.x + BLEED}em ${HOOK.y + BLEED}em` }}>
          <i className={`${LAYER} ${DIMMED} bg-[url(/objects/mat/lamp-chain.avif)]`} />
          <i data-lit={lit} className={`${LAYER} ${GLOW} bg-[url(/objects/mat/lamp-chain-glow.avif)]`} />
        </span>
      </span>
    </button>
  )
}
