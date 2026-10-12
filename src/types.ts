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

export type Profile = {
  handle: string
  role: string
  headline: { before: string; accent: string; after: string }
  intro: string[]
  works: Work[]
  now: string
  questions: Question[]
  socials: Social[]
  email: string
  colophon: string
}
