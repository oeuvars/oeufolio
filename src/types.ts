export type NavItem = {
  to: '/' | '/likes' | '/work' | '/extras' | '/contact'
  label: string
}

/** Which version of a page to show, when it is not the current one: the work page's building is v 1. */
export type VersionSearch = {
  v?: 1
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

/** The resume as a PDF, and the render of it rolled up that links to it. */
export type Resume = {
  href: string
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
  | 'card'
  | 'proraso'
  | 'razor'
  | 'wallet'
  | 'pick-fin'
  | 'pick-wedge'
  | 'catlamp'

/** One rendered picture of the desk: wide for a mat in a window, tall for a phone. */
export type PlateId = 'wide' | 'tall'

/**
 * A plate as studio/desk/desk.py renders it, in em of the plate. size is its width and height, and bleed how far
 * the lamp's light map runs past it on each side. rim is the colour of the lamp's light where its map ends, and
 * dark the colour of the lamp-off map of the light where it ends. eye is where the camera is held: x and y on the plate and its
 * height. at is where each object lies on it: the middle of its box
 * and its turn in degrees, clockwise.
 */
export type Plate = {
  size: [number, number]
  bleed: [number, number]
  rim: string
  dark: string
  eye: [number, number, number]
  at: Partial<Record<PropId, [number, number, number]>>
}

export type Profile = {
  handle: string
  nav: NavItem[]
  badge: Badge
  letter: Letter
  resume: Resume
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
