import type { Act, Pose, Rig } from '../types'
import { lasting, play } from './acts'

// Breaths a second, and how far the body swells with each: a resting cat's, and a sleeping cat's slower, deeper ones.
const BREATH = { awake: [0.5, 0.035], asleep: [0.36, 0.045] } as const
// The seconds a cat rests between one act and the next on the same track, the shortest and the longest.
const REST = { awake: [1.2, 4.5], asleep: [3, 9] } as const

type Track = {
  acts: Act[]
  playing: { act: Act; start: number; lasts: number; side: number } | null
  next: number
  last: Act | null
}

/** A small seeded random number generator (mulberry32), so each cat keeps its own habits from one visit to the next. */
const seeded = (seed: number) => () => {
  seed = (seed + 0x6d2b79f5) | 0
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}

/** An unhurried wobble between -1 and 1, about `rate` times a second, never quite repeating. */
const drift = (t: number, rate: number, phase: number) =>
  0.6 * Math.sin(2 * Math.PI * rate * t + phase) + 0.4 * Math.sin(2 * Math.PI * rate * 1.73 * t + 2.1 * phase)

/**
 * What the cat does from moment to moment. It always breathes, a little unevenly, and an awake cat's head and tail
 * never sit quite still. Now and then it does something: it tilts its head, washes a paw, swishes or flicks its tail,
 * twitches an ear. The head and paws act on one track and the tail and legs on another, so a cat may flick its tail
 * as it grooms, but never does two things at once with the same part.
 */
export class Behaviour {
  private readonly random: () => number
  private readonly tracks: Track[]
  private breath = 0
  private then: number | null = null

  constructor(
    private readonly rig: Rig,
    seed: number,
  ) {
    this.random = seeded(seed)
    this.tracks = (['front', 'back'] as const)
      .map((track) => rig.acts.filter((act) => act.track === track))
      .filter((acts) => acts.length)
      .map((acts) => ({ acts, playing: null, next: -1, last: null }))
  }

  /** The pose at `now` seconds, written into `pose` from rest. */
  pose(now: number, pose: Pose) {
    for (const part of Object.values(pose)) {
      part.angles.fill(0)
      part.shift[0] = 0
      part.shift[1] = 0
      part.swell = 0
    }
    // Back from a hidden tab, the cat carries on from where it was, not from where the clock now is.
    const step = this.then === null ? 0 : Math.min(0.1, Math.max(0, now - this.then))
    this.then = now
    this.idle(now, step, pose)
    for (const track of this.tracks) this.act(track, now, pose)
  }

  private idle(now: number, step: number, pose: Pose) {
    const { mood, breath, head, tail } = this.rig
    const [rate, depth] = BREATH[mood]
    // Each breath a little quicker or slower than the last; in quicker than out, and a pause before the next.
    this.breath += step * rate * (1 + 0.12 * drift(now, 0.05, 1.3))
    const cycle = this.breath % 1
    const lungs = cycle < 0.38 ? 0.5 - 0.5 * Math.cos((Math.PI * cycle) / 0.38) : 0.5 + 0.5 * Math.cos((Math.PI * (cycle - 0.38)) / 0.5)
    pose[breath].swell += depth * (cycle < 0.88 ? lungs : 0)
    const awake = mood === 'awake'
    if (head) pose[head].angles[0] += (awake ? 2.2 : 0.5) * drift(now, awake ? 0.09 : 0.04, 0.4)
    if (tail) {
      const angles = pose[tail].angles
      const sway = (awake ? 3.5 : 1) * drift(now, awake ? 0.17 : 0.06, 2.7)
      angles[angles.length - 1] += sway
      if (angles.length > 1) angles[angles.length - 2] += 0.6 * sway
    }
  }

  private act(track: Track, now: number, pose: Pose) {
    if (track.next < 0) track.next = now + 0.4 + 2.5 * this.random()
    if (track.playing && now - track.playing.start >= track.playing.lasts) {
      const [least, most] = REST[this.rig.mood]
      track.playing = null
      track.next = now + least + (most - least) * this.random()
    }
    if (!track.playing && now >= track.next) {
      const act = this.choose(track)
      track.playing = { act, start: now, lasts: lasting(act.kind, this.random()), side: act.side ?? (this.random() < 0.5 ? -1 : 1) }
      track.last = act
    }
    const playing = track.playing
    if (playing) play(playing.act, now - playing.start, playing.lasts, playing.side, pose)
  }

  /** Any of the track's acts by its weight, but not the one it has just done, if it has others. */
  private choose(track: Track) {
    const open = track.acts.length > 1 ? track.acts.filter((act) => act !== track.last) : track.acts
    let pick = this.random() * open.reduce((sum, act) => sum + act.weight, 0)
    for (const act of open) {
      pick -= act.weight
      if (pick <= 0) return act
    }
    return open[open.length - 1]
  }
}
