type PageTitleProps = {
  before: string
  accent: string
  after: string
}

export const PageTitle = ({ before, accent, after }: PageTitleProps) => {
  return (
    <h1 className="display text-[clamp(1.35rem,4.4vw,4.6rem)] text-balance">
      {before}
      <span className="mark">{accent}</span>
      {after}
    </h1>
  )
}
