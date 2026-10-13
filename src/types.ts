export type NavItem = {
  to: '/' | '/likes' | '/work' | '/extras'
  label: string
}

export type Work = {
  title: string
  summary: string
  category: string
  year: string
  href: string
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

export type Like = {
  title: string
  tag: string
  note: string
  details?: string[]
}

export type Role = {
  period: string
  role: string
  org: string
  summary: string
}

export type Plate = {
  title: string
  caption: string
  image?: string
}

export type Playlist = {
  title: string
  note: string
  href: string
  embed?: string
}

export type Profile = {
  handle: string
  nav: NavItem[]
  badge: Badge
  likes: Like[]
  experience: Role[]
  works: Work[]
  extras: { plates: Plate[]; playlist: Playlist }
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
