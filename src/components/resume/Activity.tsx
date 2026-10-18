import { useEffect, useState } from 'react'

type Day = { date: string; count: number; level: number }
type Year = { total: number; days: Day[] }

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const SHADES = [
  'bg-zinc-100 dark:bg-zinc-800',
  'bg-zinc-300 dark:bg-zinc-600',
  'bg-zinc-500 dark:bg-zinc-500',
  'bg-zinc-700 dark:bg-zinc-300',
  'bg-zinc-950 dark:bg-zinc-100',
]
const CELL = 'aspect-square w-full rounded-[2px]'

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
 * months spread over the year above it. Until the numbers arrive it shows an empty year, pulsing.
 */
export function Activity({ year, user }: { year: Year | null | 'failed'; user: string }) {
  if (year === 'failed') {
    return (
      <p className="py-4 text-[13px] text-zinc-500 dark:text-zinc-400">
        The contribution graph is on{' '}
        <a href={`https://github.com/${user}`} className="underline decoration-dotted underline-offset-2 hover:text-zinc-900 dark:hover:text-zinc-200">
          github.com/{user}
        </a>
        .
      </p>
    )
  }

  const loaded = year !== null
  const days: Day[] = loaded ? year.days : Array.from({ length: 364 }, () => ({ date: '', count: 0, level: 0 }))
  const lead = loaded ? new Date(`${year.days[0].date}T00:00:00Z`).getUTCDay() : 0
  const cells: (Day | null)[] = [...Array.from({ length: lead }, () => null), ...days]
  const weeks = Array.from({ length: Math.ceil(cells.length / 7) }, (_, i) => cells.slice(i * 7, i * 7 + 7))
  const first = loaded ? Number(year.days[0].date.slice(5, 7)) - 1 : 0
  const months = Array.from({ length: loaded ? 13 : 12 }, (_, i) => MONTHS[(first + i) % 12])

  return (
    <div className="relative py-4">
      <div className="w-full">
        <div aria-hidden="true" className="mb-2 flex w-full justify-between text-[10px] text-zinc-400 dark:text-zinc-500">
          {months.map((month, i) => (
            <span key={i}>{month}</span>
          ))}
        </div>
        <div
          role="img"
          aria-label={loaded ? `${year.total} GitHub contributions in the last year` : 'Loading GitHub contribution activity'}
          className="grid gap-x-[2px]"
          style={{ gridTemplateColumns: `repeat(${weeks.length}, minmax(0, 1fr))` }}
        >
          {weeks.map((week, w) => (
            <div key={w} className="flex flex-col gap-[2px]">
              {Array.from({ length: 7 }, (_, d) => {
                const day = week[d]
                if (!day) return <div key={d} className={`${CELL} bg-transparent`} />
                if (!loaded) return <div key={d} className={`${CELL} animate-pulse bg-zinc-100 dark:bg-zinc-800`} />
                return (
                  <div
                    key={d}
                    title={`${day.count} on ${day.date}`}
                    className={`${CELL} opacity-80 outline-none transition-[opacity,transform] hover:scale-125 hover:opacity-100 dark:opacity-70 dark:hover:opacity-100 ${SHADES[day.level]}`}
                  />
                )
              })}
            </div>
          ))}
        </div>
      </div>
      <div aria-hidden="true" className="mt-3 flex items-center justify-between gap-3">
        <span className="text-[11px] text-zinc-500 dark:text-zinc-400">Less active</span>
        <div className="flex shrink-0 items-center gap-1.5">
          {SHADES.map((shade) => (
            <div key={shade} className={`size-2 rounded-[2px] opacity-80 dark:opacity-70 ${shade}`} />
          ))}
          <span className="text-[11px] text-zinc-500 dark:text-zinc-400">More active</span>
        </div>
      </div>
    </div>
  )
}
