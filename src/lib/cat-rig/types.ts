// What a cat cut out of a photograph is rigged with, and what it is told to do. Every length and point is in pixels of
// the cut-out's own picture, y down; every angle in degrees, clockwise as the picture shows it.

export type Point = [number, number]

/**
 * How a part follows where the cat means it to be: a damped spring, `rate` its stiffness (radians a second) and
 * `damping` its damping ratio, 1 to settle without overshooting. Along a chain they ease from the root's to `tip`'s,
 * so a slower, looser tip trails the root and swings through after it.
 */
export type Spring = {
  rate: number
  damping: number
  tip?: { rate: number; damping: number }
}

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
  spring: Spring
  /** Parts whose hold on the picture comes before this one's where both reach. */
  yields?: string[]
}

/**
 * The breathing body: the picture swells out from `centre`, whole inside the ellipse, letting go over `soft`; mostly
 * along `across` (degrees from the picture's x axis), the way the ribs widen, and a quarter as much the other way.
 */
export type Swell = {
  kind: 'swell'
  centre: Point
  radii: Point
  soft: number
  across: number
}

export type Part = Chain | Swell

type Played = {
  /** How often it is chosen beside the others on its track. */
  weight: number
  /** Acts on the same track wait for one another; the head and paws act while the tail does. */
  track: 'front' | 'back'
}

export type Act = Played &
  (
    // The head goes over to a new way of holding itself and stays there: `roll` the most it turns either way.
    | { kind: 'look'; head: string; roll: Point; reach: Point }
    // A bout of washing a paw: down to it, then about a lick a second, each a push of the paw and a roll of the head.
    | { kind: 'groom'; head: string; paws: string[]; bow: number; reach: Point; lift: Point; roll: number; strokes: Point }
    | { kind: 'knead'; paws: [string, string]; push: Point }
    // The tail is laid somewhere new across the desk, `deg` at its root and `curl` along it, and left there.
    | { kind: 'sweep'; tail: string; deg: number; curl: number }
    // The tip of the tail flicks and whips back.
    | { kind: 'flick'; tail: string; deg: number }
    // An ear or a foot jerks `deg` (its sign the way it goes) and springs back.
    | { kind: 'twitch'; part: string; deg: number }
    | { kind: 'stretch'; part: string; deg: number; reach: Point }
    // A sleeping head shifts a little where it lies.
    | { kind: 'settle'; head: string; deg: number }
  )

export type ActKind = Act['kind']

/** One cat: its parts, whether it is awake, which part breathes, and what it may do. */
export type Rig = {
  mood: 'awake' | 'asleep'
  parts: Record<string, Part>
  breath: string
  acts: Act[]
}

/** Where each part is: each bone's turn, the part's shift, and how far it has swollen. */
export type PartPose = {
  angles: number[]
  shift: Point
  swell: number
}

export type Pose = Record<string, PartPose>
