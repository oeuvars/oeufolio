import { useEffect, useState } from 'react'

const ZONE = 'Asia/Kolkata'
const timeFormat = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: ZONE })
const dateFormat = new Intl.DateTimeFormat('en-GB', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  timeZone: ZONE,
})

/**
 * Wall clock and calendar date in Kolkata, refreshed twice a minute. Both are empty until the page has
 * mounted, so that the server does not print a time of its own.
 */
export function useKolkata() {
  const [now, setNow] = useState<Date | null>(null)

  useEffect(() => {
    setNow(new Date())
    const timer = window.setInterval(() => setNow(new Date()), 30_000)
    return () => window.clearInterval(timer)
  }, [])

  return { time: now ? timeFormat.format(now) : '', date: now ? dateFormat.format(now) : '' }
}
