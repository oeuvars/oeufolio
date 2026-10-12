import { useEffect, useState } from 'react'

export function Clock() {
  const [now, setNow] = useState<Date | null>(null)

  useEffect(() => {
    setNow(new Date())
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  if (!now) return <span className="opacity-0">00:00:00</span>

  const time = now.toLocaleTimeString('en-GB', { hour12: false })
  const zone = new Intl.DateTimeFormat('en', { timeZoneName: 'short' })
    .formatToParts(now)
    .find((part) => part.type === 'timeZoneName')?.value
  return (
    <span className="tabular-nums">
      {time} {zone}
    </span>
  )
}
