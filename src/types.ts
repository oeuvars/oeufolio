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

/** The resume as a PDF, the photograph of the desk with it rolled up on it, and the name of the link to it. */
export type Resume = {
  href: string
  src: string
  alt: string
}

export type Role = {
  period: string
  org: string
}

/**
 * A company named in the work poster's passages, where studio/poster/type.mjs found it, in the reference poster's
 * pixels: the word's ends, its baseline and its type size. The poster runs a highlighter over it; the page links it.
 */
export type PosterMark = {
  label: string
  href: string
  left: number
  right: number
  baseline: number
  size: number
}

/** studio/poster/type.mjs's measure of the poster's passages: the reference's size and the companies in them. */
export type PosterMarks = {
  size: [number, number]
  marks: PosterMark[]
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
  | 'donutlamp'
  | 'ilolamp'
  | 'flutelamp'
  | 'lustrelamp'
  | 'mushroomlamp'

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

/** A rectangle of a plate, in its em: left, top, width and height. */
export type Rect = [number, number, number, number]

/**
 * Props the desk shows from a low camera of their own, as each was photographed, laid over the plate: for each, the
 * rectangle of the plate its picture covers, glow and all, and the rectangle the prop itself fills.
 */
export type Portraits = Partial<Record<PropId, { picture: Rect; body: Rect }>>

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

/** A job on the résumé, as resume.pdf has it. */
export type CvRole = {
  company: string
  /** What the company is, as the PDF puts it after the name. */
  about?: string
  href: string
  place: string
  title: string
  period: string
  points: string[]
}

export type CvSchool = {
  course: string
  school: string
  grade: string
}

/** The résumé as a page of text (src/routes/resume.tsx), word for word what resume.pdf says. */
export type Cv = {
  name: string
  headline: string
  roles: CvRole[]
  skills: Credit[]
  education: CvSchool[]
}

/** Where a word on the error page's photograph lies (studio/error/book.py): its text, its box as fractions of the
 * plate (left, top, width, height), and whether it runs down the page. */
export type ErrorPlace = {
  text: string
  box: number[]
  vertical: boolean
}

/** One photograph of the error page's book: its size in pixels, the part of it the pages cover (left, top, right,
 * bottom, as fractions), the colour its edges fall to, and where each of its words lies. */
export type ErrorPlate = {
  size: number[]
  pages: number[]
  edge: string
  boxes: Record<string, ErrorPlace>
}

/** Where the site lives and who it is, for the tags that describe every page to search engines and link previews. */
export type Site = {
  url: string
  name: string
  /** The X handle, with its @. */
  x: string
  locale: string
}

/** The picture a link to a page unfurls into: a 1200 by 630 capture of the page (public/og). */
export type Preview = {
  src: string
  alt: string
}

/** How a page describes itself: its address, its title and summary, and its link preview. */
export type PageMeta = {
  path: string
  title: string
  description: string
  preview: Preview
}

export type PageId = 'basics' | 'likes' | 'work' | 'extras' | 'contact' | 'resume'

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
