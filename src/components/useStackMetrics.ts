import { useEffect, useState } from 'react'

import type { StackMetrics } from '../types'

const clamp = (min: number, value: number, max: number) => Math.min(max, Math.max(min, value))

const fallback: StackMetrics = {
  width: 1440,
  height: 900,
  rem: 16,
  mobile: false,
  overlap: 16,
  band: 30.4,
  protrude: 33.6,
  strip: clamp(128, 172.8, 208),
  spine: clamp(104, 153, 160),
  contact: clamp(112, 129.6, 160),
  end: 51.2,
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
    overlap: rem,
    band: (mobile ? 1.4 : 1.9) * rem,
    protrude: (mobile ? 1.5 : 2.1) * rem,
    strip: mobile ? 3.6 * rem : clamp(8 * rem, 0.12 * width, 13 * rem),
    spine: clamp(6.5 * rem, 0.17 * height, 10 * rem),
    contact: clamp(7 * rem, 0.09 * width, 10 * rem),
    end: 3.2 * rem,
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
