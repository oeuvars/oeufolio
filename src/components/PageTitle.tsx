import { HandCircle } from './HandCircle'

type PageTitleProps = {
  before: string
  accent: string
  after: string
  circled?: boolean
}

export function PageTitle({ before, accent, after, circled = false }: PageTitleProps) {
  const accentWord = <em className="foil font-accent">{accent}</em>
  return (
    <h1 className="ink text-[clamp(2.4rem,5.4vw,5.2rem)] leading-[1.02] font-normal tracking-[-0.012em] text-balance">
      {before}
      {circled ? <HandCircle>{accentWord}</HandCircle> : accentWord}
      {after}
    </h1>
  )
}
