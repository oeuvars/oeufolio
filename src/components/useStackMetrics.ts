import { useEffect, useState } from 'react'

import type { StackMetrics } from '../types'

const clamp = (min: number, value: number, max: number) => Math.min(max, Math.max(min, value))

const fallback: StackMetrics = {
  width: 1440,
  height: 900,
  rem: 16,
  mobile: false,
  overlap: 14.4,
  tab: 48,
  strip: clamp(96, 151.2, 160),
  spine: clamp(86.4, 144, 144),
  contact: clamp(96, 144, 144),
}

function measure(): StackMetrics {
  const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16
  const width = window.innerWidth
  const height = window.innerHeight
  const mobile = width < 768

  return {
    width,
    height,
    rem,
    mobile,
    overlap: 0.9 * rem,
    tab: (mobile ? 2.4 : 3) * rem,
    strip: mobile ? 3.1 * rem : clamp(6 * rem, 0.105 * width, 10 * rem),
    spine: mobile ? 0 : clamp(5.4 * rem, 0.16 * height, 9 * rem),
    contact: mobile ? 0 : clamp(6 * rem, 0.1 * width, 9 * rem),
  }
}

/** Viewport-derived sheet geometry in pixels, so sheets can be positioned by spring animation. */
export function useStackMetrics() {
  const [metrics, setMetrics] = useState<StackMetrics>(fallback)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const update = () => setMetrics(measure())
    update()
    const frame = requestAnimationFrame(() => setReady(true))
    window.addEventListener('resize', update)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', update)
    }
  }, [])

  return { metrics, ready }
}
