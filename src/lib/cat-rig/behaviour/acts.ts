import type { Act, ActKind, Pose } from '../types'

// How long each act may last, in seconds, the shortest and the longest.
const LASTS: Record<ActKind, [number, number]> = {
  tilt: [2.2, 4.5],
  look: [1.8, 3.4],
  groom: [3.6, 6.5],
  knead: [2.6, 4.6],
  swish: [2.6, 5.2],
  flick: [0, 0],
  twitch: [0, 0],
  stretch: [2.8, 4.2],
  nestle: [4, 6.5],
}
// A flick or a twitch is over in a moment, and comes once or twice: how long one takes.
const FLICK = 0.42
const TWITCH = 0.38

/** How long this act lasts this time, given a random number between 0 and 1. */
export const lasting = (kind: ActKind, chance: number) => {
  if (kind === 'flick') return chance < 0.6 ? FLICK : 2 * FLICK
  if (kind === 'twitch') return chance < 0.5 ? TWITCH : 2 * TWITCH
  const [least, most] = LASTS[kind]
  return least + chance * (most - least)
}

const clamp = (x: number) => Math.min(1, Math.max(0, x))
const ease = (x: number) => {
  const t = clamp(x)
  return t * t * (3 - 2 * t)
}

/** 0 at the act's start and end, 1 between, coming in over `rise` seconds and going over `fall`. */
const envelope = (t: number, lasts: number, rise: number, fall: number) => ease(t / rise) * ease((lasts - t) / fall)

/** A quick move out and a slower one back, repeated every `period` seconds. */
const jerk = (t: number, period: number) => {
  const u = t % period
  const out = 0.18 * period
  return u < out ? ease(u / out) : 1 - ease((u - out) / (period - out))
}

/**
 * Adds one act, `t` seconds into it, to the pose. `side` is which way it goes this time (1 or -1); the act's own
 * numbers are how far it goes at most.
 */
export const play = (act: Act, t: number, lasts: number, side: number, pose: Pose) => {
  switch (act.kind) {
    case 'tilt': {
      // The head goes over quickly and is held there, a little unsteadily, then comes back up.
      const e = envelope(t, lasts, 0.35, 0.75)
      pose[act.head].angles[0] += side * act.deg * e * (1 + 0.06 * Math.sin(2 * Math.PI * 0.8 * t))
      return
    }
    case 'look': {
      const e = envelope(t, lasts, 0.3, 0.6)
      const head = pose[act.head]
      head.angles[0] += side * act.deg * e
      head.shift[0] += side * act.reach[0] * e
      head.shift[1] += act.reach[1] * e
      return
    }
    case 'groom': {
      // Down to the paw as the paw comes up to it, then the tongue's strokes, two or three a second, each a dip of
      // the head and a nudge of the paw.
      const e = envelope(t, lasts, 0.7, 0.8)
      const stroke = e * (0.5 - 0.5 * Math.cos(2 * Math.PI * 2.6 * Math.max(0, t - 0.7)))
      const head = pose[act.head]
      head.angles[0] += act.bow * (e + 0.35 * stroke)
      head.shift[0] += act.reach[0] * (e + 0.3 * stroke)
      head.shift[1] += act.reach[1] * (e + 0.3 * stroke)
      for (const name of act.paws) {
        const paw = pose[name]
        paw.shift[0] += act.lift[0] * (e - 0.2 * stroke)
        paw.shift[1] += act.lift[1] * (e - 0.2 * stroke)
      }
      return
    }
    case 'knead': {
      const e = envelope(t, lasts, 0.4, 0.6)
      act.paws.forEach((name, i) => {
        const push = e * Math.max(0, Math.sin(2 * Math.PI * 1.3 * t + i * Math.PI))
        const paw = pose[name]
        paw.shift[0] += act.push[0] * push
        paw.shift[1] += act.push[1] * push
        paw.angles[0] += 5 * push * (i ? 1 : -1)
      })
      return
    }
    case 'swish': {
      // A slow wave down the tail, its tip swinging furthest, side to side over the desk.
      const e = envelope(t, lasts, 0.8, 1)
      const angles = pose[act.tail].angles
      const total = (angles.length * (angles.length + 1)) / 2
      for (let b = 0; b < angles.length; b++) {
        angles[b] += act.deg * ((b + 1) / total) * e * Math.sin(2 * Math.PI * 0.55 * t - 0.9 * b + (side > 0 ? 0 : Math.PI))
      }
      return
    }
    case 'flick': {
      const angles = pose[act.tail].angles
      const k = side * act.deg * jerk(t, FLICK)
      angles[angles.length - 1] += k
      if (angles.length > 1) angles[angles.length - 2] += 0.5 * k
      return
    }
    case 'twitch': {
      pose[act.part].angles[0] += side * act.deg * jerk(t, TWITCH)
      return
    }
    case 'stretch': {
      const e = envelope(t, lasts, 1, 1.3)
      const part = pose[act.part]
      part.angles[0] += act.deg * e
      part.shift[0] += act.reach[0] * e
      part.shift[1] += act.reach[1] * e
      return
    }
    case 'nestle': {
      const e = envelope(t, lasts, 1.4, 2.2)
      pose[act.head].angles[0] += side * act.deg * e
      return
    }
  }
}
