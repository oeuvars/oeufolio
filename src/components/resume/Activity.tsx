import { useEffect, useState } from 'react'

type Day = { date: string; count: number; level: number }
type Year = { total: number; days: Day[] }

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const SHADES = ['bg-(--l0)', 'bg-(--l1)', 'bg-(--l2)', 'bg-(--l3)', 'bg-(--l4)']

/** The last year of a GitHub user's public contributions, from the open contributions API GitHub's own graph feeds. */
export function useActivity(user: string) {
  const [year, setYear] = useState<Year | null | 'failed'>(null)

  useEffect(() => {
    let live = true
    fetch(`https://github-contributions-api.jogruber.de/v4/${user}?y=last`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
      .then((data: { total: { lastYear: number }; contributions: Day[] }) => {
        if (live) setYear({ total: data.total.lastYear, days: data.contributions })
      })
      .catch(() => live && setYear('failed'))
    return () => {
      live = false
    }
  }, [user])

  return year
}

/**
 * The contribution grid: a column a week, Sunday at the top, each day shaded by how much was pushed that day, with the
 * month named over the week it starts in. Until the numbers arrive it shows an empty year.
 */
export function Activity({ year, user }: { year: Year | null | 'failed'; user: string }) {
  if (year === 'failed') {
    return (
      <p className="px-4 py-6 text-[13px] text-(--muted)">
        The contribution graph is on{' '}
        <a href={`https://github.com/${user}`} className="text-(--ink) underline decoration-(--line) underline-offset-2">
          github.com/{user}
        </a>
        .
      </p>
    )
  }

  const days: (Day | null)[] = year ? year.days : Array.from({ length: 365 }, () => ({ date: '', count: 0, level: 0 }))
  const lead = year ? new Date(`${year.days[0].date}T00:00:00Z`).getUTCDay() : 0
  const cells = [...Array.from({ length: lead }, () => null), ...days]
  const weeks = Array.from({ length: Math.ceil(cells.length / 7) }, (_, i) => cells.slice(i * 7, i * 7 + 7))

  let last = -4
  const labels = weeks.map((week, i) => {
    const first = week.find((day) => day?.date && Number(day.date.slice(8)) <= 7)
    if (!first?.date || i - last < 3) return ''
    last = i
    return MONTHS[Number(first.date.slice(5, 7)) - 1]
  })

  return (
    <div className="px-4 pt-5 pb-6">
      <div className="overflow-x-auto pb-1">
        <div className="min-w-[520px]">
          <div aria-hidden="true" className="grid gap-[3px] text-[10px] text-(--faint)" style={{ gridTemplateColumns: `repeat(${weeks.length}, minmax(0, 1fr))` }}>
            {labels.map((label, i) => (
              <span key={i} className="h-4 overflow-visible whitespace-nowrap">
                {label}
              </span>
            ))}
          </div>
          <div
            role="img"
            aria-label={year ? `${year.total} contributions on GitHub in the last year` : 'Loading contributions'}
            className="mt-1 grid grid-flow-col grid-rows-7 gap-[3px]"
            style={{ gridTemplateColumns: `repeat(${weeks.length}, minmax(0, 1fr))` }}
          >
            {weeks.flatMap((week, w) =>
              Array.from({ length: 7 }, (_, d) => {
                const day = week[d]
                return (
                  <span
                    key={`${w}-${d}`}
                    title={day?.date ? `${day.count} on ${day.date}` : undefined}
                    className={`aspect-square rounded-[2px] ${day ? SHADES[day.level] : ''} ${year ? '' : 'animate-pulse'}`}
                  />
                )
              }),
            )}
          </div>
        </div>
      </div>
      <div aria-hidden="true" className="mt-3 flex items-center justify-between text-[11px] text-(--muted)">
        <span>Less active</span>
        <span className="flex items-center gap-[3px]">
          {SHADES.map((shade) => (
            <span key={shade} className={`size-2 rounded-[2px] ${shade}`} />
          ))}
          <span className="ml-1">More active</span>
        </span>
      </div>
    </div>
  )
}
