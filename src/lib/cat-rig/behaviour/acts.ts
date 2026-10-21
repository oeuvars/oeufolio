import type { Act, Pose } from '../types'

/** One act under way: when it began, how long it lasts, which way it goes, and how many strokes or beats it has. */
export type Playing = {
  act: Act
  start: number
  lasts: number
  side: number
  count: number
}

// The timings below are measured from footage of real cats (Pexels and Wikimedia Commons clips, tracked frame by
// frame): a wash is about a lick a second, a kneading paw pushes a little more often, a tail tip or an ear is out and
// back within half a second, and a stretch is held for a breath or two.
const LICK = 1.05
const KNEAD = 0.8
const APPROACH = 1

const between = ([least, most]: [number, number], chance: number) => least + chance * (most - least)
const ease = (x: number) => {
  const t = Math.min(1, Math.max(0, x))
  return t * t * (3 - 2 * t)
}

/**
 * A jerk and its rebound: out within `out` seconds, then back past where it started and settling, a little lower each
 * swing, `decay` the seconds it takes to fall to a third and `swing` the seconds of each swing. The shape of a tail tip
 * flicking or an ear flicking a fly off, which a spring driven to a new place does not have.
 */
const whip = (u: number, out: number, decay: number, swing: number) => {
  if (u < 0) return 0
  if (u < out) return Math.sin((Math.PI / 2) * (u / out)) ** 2
  const v = u - out
  return Math.exp(-v / decay) * Math.cos((2 * Math.PI * v) / swing)
}

/**
 * Starts an act: how long it will last, and, for the acts that leave the cat holding itself differently, the new way
 * it holds itself, written into `held`, which it keeps until another act moves it.
 */
export const begin = (act: Act, start: number, random: () => number, held: Pose): Playing => {
  const side = random() < 0.5 ? -1 : 1
  const playing: Playing = { act, start, lasts: 0, side, count: 1 }
  switch (act.kind) {
    case 'look': {
      const head = held[act.head]
      // A cat looks back to where it was about as often as it looks somewhere new, and small moves are commoner.
      const away = head.angles[0] !== 0 && random() < 0.45
      const [left, right] = act.roll
      const roll = away ? 0 : (side < 0 ? left : right) * (0.25 + 0.75 * random() ** 1.5)
      const share = roll / (roll < 0 ? -left || 1 : right || 1)
      head.angles[0] = roll
      head.shift[0] = act.reach[0] * share
      head.shift[1] = act.reach[1] * Math.abs(share)
      return playing
    }
    case 'sweep': {
      const tail = held[act.tail].angles
      const away = tail.some((angle) => angle !== 0) && random() < 0.4
      const root = away ? 0 : side * act.deg * (0.4 + 0.6 * random())
      const curl = away ? 0 : (random() * 2 - 1) * act.curl
      tail.fill(0)
      tail[0] = root
      // The curl grows toward the tip, as a lying cat's tail bends more the further it is from the root.
      const share = (tail.length * (tail.length - 1)) / 2
      for (let b = 1; b < tail.length; b++) tail[b] = (curl * b) / share
      return playing
    }
    case 'settle': {
      held[act.head].angles[0] = random() < 0.4 ? 0 : side * act.deg * (0.4 + 0.6 * random())
      return playing
    }
    case 'groom': {
      // The head comes back from wherever it was looking when the wash is over.
      held[act.head].angles[0] = 0
      held[act.head].shift = [0, 0]
      playing.count = Math.round(between(act.strokes, random()))
      playing.lasts = APPROACH + playing.count * LICK + 0.3
      return playing
    }
    case 'knead':
      playing.count = 3 + Math.floor(random() * 4)
      playing.lasts = playing.count * KNEAD + 0.2
      return playing
    case 'flick':
      playing.count = random() < 0.65 ? 1 : 2
      playing.lasts = 0.3 + playing.count * 0.45
      return playing
    case 'twitch':
      playing.count = random() < 0.6 ? 1 : 2
      playing.lasts = 0.2 + playing.count * 0.3
      return playing
    case 'stretch':
      playing.lasts = between([2, 3.6], random())
      return playing
  }
}

/**
 * Adds an act, `t` seconds into it: where the cat means its parts to be (`target`, followed by their springs), and the
 * jerks too quick for a spring (`pulse`, added as they are).
 */
export const play = ({ act, lasts, side, count }: Playing, t: number, target: Pose, pulse: Pose) => {
  switch (act.kind) {
    case 'groom': {
      // Down to the paw on the springs, then each lick: the paw pushed up into the mouth as the head rolls down onto
      // it, the same way each time, and both drawing back, in one smooth swing about a second long.
      const near = t > 0.05 && t < lasts - 0.3 ? 1 : 0
      const u = t - APPROACH
      const stroke = u > 0 && u < count * LICK ? 0.5 - 0.5 * Math.cos((2 * Math.PI * u) / LICK) : 0
      const head = target[act.head]
      head.angles[0] += act.bow * near
      head.shift[0] += act.reach[0] * near
      head.shift[1] += act.reach[1] * near
      const lick = pulse[act.head]
      lick.angles[0] += act.roll * stroke * side
      lick.shift[0] += act.reach[0] * 0.35 * stroke
      lick.shift[1] += act.reach[1] * 0.35 * stroke
      for (const name of act.paws) {
        target[name].shift[0] += act.lift[0] * near
        target[name].shift[1] += act.lift[1] * near
        pulse[name].shift[0] += act.lift[0] * 0.4 * stroke
        pulse[name].shift[1] += act.lift[1] * 0.4 * stroke
      }
      return
    }
    case 'knead': {
      // Each paw in turn pressed down and let up, smoothly, as a cat treads.
      if (t > count * KNEAD) return
      act.paws.forEach((name, i) => {
        const press = Math.max(0, Math.sin((Math.PI * t) / KNEAD - i * Math.PI)) ** 2
        const paw = pulse[name]
        paw.shift[0] += act.push[0] * press
        paw.shift[1] += act.push[1] * press
        paw.angles[0] += 6 * press * (i ? 1 : -1)
      })
      return
    }
    case 'stretch': {
      if (t < lasts - 0.9) {
        const part = target[act.part]
        part.angles[0] += act.deg
        part.shift[0] += act.reach[0]
        part.shift[1] += act.reach[1]
      }
      return
    }
    case 'flick': {
      const angles = pulse[act.tail].angles
      let k = 0
      for (let n = 0; n < count; n++) k += whip(t - n * 0.45, 0.09, 0.1, 0.34)
      angles[angles.length - 1] += side * act.deg * k
      if (angles.length > 1) angles[angles.length - 2] += side * act.deg * 0.45 * whip(t - 0.03, 0.09, 0.1, 0.34)
      return
    }
    case 'twitch': {
      let k = 0
      for (let n = 0; n < count; n++) k += whip(t - n * 0.3, 0.05, 0.05, 0.22)
      // Always the same way: an ear flicks out and back, a foot jerks the way its joint bends.
      pulse[act.part].angles[0] += act.deg * k * ease((lasts - t) / 0.1)
      return
    }
    default:
      return
  }
}
