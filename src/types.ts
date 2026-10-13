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

export type Question = {
  q: string
  a: string
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
  basics: {
    headline: { before: string; accent: string; after: string }
    intro: string[]
    now: string
    questions: Question[]
  }
  likes: Like[]
  experience: Role[]
  works: Work[]
  extras: { plates: Plate[]; playlist: Playlist }
  socials: Social[]
  email: string
  colophon: string
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
