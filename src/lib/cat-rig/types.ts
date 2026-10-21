// What a cat cut out of a photograph is rigged with, and what it is told to do. Every length and point is in pixels of
// the cut-out's own picture, y down; every angle in degrees, clockwise as the picture shows it.

export type Point = [number, number]

/**
 * A run of bones through a part of the cat that bends: a tail, a head on its neck, a paw on its leg. The first joint
 * is the pivot the part turns on; each bone turns on its joint and carries the bones past it. The part holds the
 * picture as far as `reach` from its bones (given at each joint, eased between), and lets go over `soft` past that.
 */
export type Chain = {
  kind: 'chain'
  joints: Point[]
  reach: number[]
  soft: number
  /** Parts whose hold on the picture comes before this one's where both reach. */
  yields?: string[]
}

/** The breathing body: the picture swells out from `centre`, whole inside the ellipse, letting go over `soft`. */
export type Swell = {
  kind: 'swell'
  centre: Point
  radii: Point
  soft: number
}

export type Part = Chain | Swell

type Played = {
  /** How often it is chosen beside the others on its track. */
  weight: number
  /** Acts on the same track wait for one another; the head and paws act while the tail does. */
  track: 'front' | 'back'
  /** The one way it goes, clockwise (1) or not (-1), where the cat has no room the other way; either, if unset. */
  side?: 1 | -1
}

export type Act = Played &
  (
    | { kind: 'tilt'; head: string; deg: number }
    | { kind: 'look'; head: string; deg: number; reach: Point }
    | { kind: 'groom'; head: string; paws: string[]; bow: number; reach: Point; lift: Point }
    | { kind: 'knead'; paws: [string, string]; push: Point }
    | { kind: 'swish'; tail: string; deg: number }
    | { kind: 'flick'; tail: string; deg: number }
    | { kind: 'twitch'; part: string; deg: number }
    | { kind: 'stretch'; part: string; deg: number; reach: Point }
    | { kind: 'nestle'; head: string; deg: number }
  )

export type ActKind = Act['kind']

/** One cat: its parts, whether it is awake, which part breathes and drifts at rest, and what it may do. */
export type Rig = {
  mood: 'awake' | 'asleep'
  parts: Record<string, Part>
  breath: string
  head?: string
  tail?: string
  acts: Act[]
}

/** Where each part is this frame: each bone's turn, the part's shift, and how far it has swollen. */
export type PartPose = {
  angles: number[]
  shift: Point
  swell: number
}

export type Pose = Record<string, PartPose>
