export type NavItem = {
  to: '/' | '/likes' | '/work' | '/extras' | '/contact'
  label: string
}

export type Social = {
  label: string
  href: string
}

export type Badge = {
  src: string
  alt: string
  backdrop: { color: string; image?: string }
}

export type Letter = {
  src: string
  alt: string
}

export type Role = {
  period: string
  org: string
}

export type Credit = {
  label: string
  value: string
}

/** The object on the mat that a like is made into. */
export type LikeProp = 'record' | 'recorder' | 'key' | 'ticket'

export type Like = {
  subject: string
  title: string
  note: string
}

export type Playlist = {
  title: string
  href: string
}

export type Extras = {
  name: string
  career: string
  company: Social
  particulars: Credit[]
  likes: Record<LikeProp, Like>
  playlist: Playlist
}

/** An object on the mat. The key is on the bunch that carries the name, so it has no place of its own. */
export type PropId =
  | Exclude<LikeProp, 'key'>
  | 'name'
  | 'particulars'
  | 'proraso'
  | 'razor'
  | 'earpods'
  | 'wallet'
  | 'pick-fin'
  | 'pick-wedge'

/** The centre of an object on the mat, in pixels, and its turn in degrees. */
export type Slot = {
  x: number
  y: number
  r: number
}

export type MatLayout = Partial<Record<PropId, Slot>>

export type Size = {
  w: number
  h: number
}

/** Sunlight over Kolkata at one moment. day and warmth run 0 to 1, dx and dy point along the shadows. */
export type Light = {
  day: number
  warmth: number
  dx: number
  dy: number
  reach: number
}

export type Profile = {
  handle: string
  nav: NavItem[]
  badge: Badge
  letter: Letter
  experience: Role[]
  extras: Extras
  socials: Social[]
  email: string
}

export type StackMetrics = {
  width: number
  height: number
  rem: number
  mobile: boolean
  overlap: number
  band: number
  protrude: number
  strip: number
  spine: number
  contact: number
  end: number
}
