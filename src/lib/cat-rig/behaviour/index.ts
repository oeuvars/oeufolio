import type { Pose, Rig } from '../types'
import { begin, play, type Playing } from './acts'
import { Springs } from './springs'

// Breaths a minute and how far the ribs widen with each, awake at rest and asleep, as the footage showed: a sleeping
// cat's back rose by about a sixtieth of its height, slowly, eleven to twenty times a minute.
const BREATH = { awake: [24, 0.022], asleep: [16, 0.028] } as const
// The seconds a cat stays still between one act and the next on each track, the shortest and the longest. Most of
// the time a cat does nothing at all.
const REST = {
  awake: { front: [4, 12], back: [5, 16] },
  asleep: { front: [8, 22], back: [10, 28] },
} as const

type Track = {
  name: 'front' | 'back'
  acts: Rig['acts']
  playing: Playing | null
  next: number
  last: Rig['acts'][number] | null
}

/** A small seeded random number generator (mulberry32), so each cat keeps its own habits from one visit to the next. */
const seeded = (seed: number) => () => {
  seed = (seed + 0x6d2b79f5) | 0
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}

const clear = (pose: Pose) => {
  for (const part of Object.values(pose)) {
    part.angles.fill(0)
    part.shift[0] = 0
    part.shift[1] = 0
    part.swell = 0
  }
}

/**
 * What the cat does from moment to moment, after footage of real cats. Mostly it lies still and breathes. Now and
 * then it does something and holds the new pose: it looks somewhere else, lays its tail elsewhere, settles its head.
 * Or it washes a paw, kneads, stretches a leg, flicks its tail or twitches an ear, and goes back to how it was. Its
 * parts get where it means them to be on springs, quick to start and slow to settle, never on a timed curve. The head
 * and paws act on one track and the tail and legs on another, so it may flick its tail as it washes.
 */
export class Behaviour {
  private readonly random: () => number
  private readonly tracks: Track[]
  private readonly springs: Springs
  private readonly held: Pose
  private readonly target: Pose
  private readonly pulse: Pose
  private breath = 0
  private pace = 1
  private then: number | null = null

  constructor(
    private readonly rig: Rig,
    seed: number,
    blank: () => Pose,
  ) {
    this.random = seeded(seed)
    this.springs = new Springs(rig)
    this.held = blank()
    this.target = blank()
    this.pulse = blank()
    this.tracks = (['front', 'back'] as const)
      .map((name) => ({ name, acts: rig.acts.filter((act) => act.track === name), playing: null, next: -1, last: null }))
      .filter((track) => track.acts.length)
  }

  /** The pose at `now` seconds, written into `pose`. */
  pose(now: number, pose: Pose) {
    // Back from a hidden tab, the cat carries on from where it was, not from where the clock now is.
    const step = this.then === null ? 0 : Math.min(0.05, Math.max(0, now - this.then))
    this.then = now
    for (const [name, part] of Object.entries(this.held)) {
      const goal = this.target[name]
      for (let b = 0; b < part.angles.length; b++) goal.angles[b] = part.angles[b]
      goal.shift[0] = part.shift[0]
      goal.shift[1] = part.shift[1]
    }
    clear(this.pulse)
    for (const track of this.tracks) this.act(track, now)
    this.springs.step(this.target, step, pose)
    for (const [name, part] of Object.entries(this.pulse)) {
      const out = pose[name]
      for (let b = 0; b < part.angles.length; b++) out.angles[b] += part.angles[b]
      out.shift[0] += part.shift[0]
      out.shift[1] += part.shift[1]
    }
    pose[this.rig.breath].swell = this.lungs(step)
  }

  /** How far the ribs are widened: in over two fifths of a breath, out over the next half, then a pause. */
  private lungs(step: number) {
    const [rate, depth] = BREATH[this.rig.mood]
    this.breath += (step * rate * this.pace) / 60
    if (this.breath >= 1) {
      this.breath -= 1
      // No two breaths quite alike.
      this.pace = 0.85 + 0.3 * this.random()
    }
    const x = this.breath
    const fill = x < 0.4 ? 0.5 - 0.5 * Math.cos((Math.PI * x) / 0.4) : x < 0.88 ? 0.5 + 0.5 * Math.cos((Math.PI * (x - 0.4)) / 0.48) : 0
    return depth * fill
  }

  private act(track: Track, now: number) {
    const rest = REST[this.rig.mood][track.name]
    if (track.next < 0) track.next = now + 0.3 * rest[0] + rest[0] * this.random()
    if (track.playing && now - track.playing.start >= track.playing.lasts) {
      track.playing = null
      track.next = now + rest[0] + (rest[1] - rest[0]) * this.random()
    }
    if (!track.playing && now >= track.next) {
      const act = this.choose(track)
      track.playing = begin(act, now, this.random, this.held)
      track.last = act
    }
    if (track.playing) play(track.playing, now - track.playing.start, this.target, this.pulse)
  }

  /** Any of the track's acts by its weight, the one it has just done a third as likely to come again. */
  private choose(track: Track) {
    const weight = (act: Track['acts'][number]) => act.weight * (act === track.last ? 1 / 3 : 1)
    let pick = this.random() * track.acts.reduce((sum, act) => sum + weight(act), 0)
    for (const act of track.acts) {
      pick -= weight(act)
      if (pick <= 0) return act
    }
    return track.acts[track.acts.length - 1]
  }
}
