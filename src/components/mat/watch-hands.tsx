import { useEffect, useRef } from 'react'

import { cn } from '../../lib/utils'
import type { PlateId } from '../../types'
import { DIALS } from './layout'

type WatchHandsProps = {
  plate: PlateId
  /** How many pixels an em of the plate is drawn. */
  em: number
  className?: string
  style?: React.CSSProperties
}

// The hands as they lie over the dial, lowest first, each with the seconds it takes to go round once.
const ROUND = [
  ['seconds', 60],
  ['hour', 12 * 3600],
  ['minute', 3600],
] as const

const load = (src: string) => {
  const image = new Image()
  image.src = src
  return image.decode().then(() => image)
}

/**
 * The watch keeps the viewer's time. Over the plate's dial lies the dial again, rendered without the hands that
 * move, and on it each of them where it has stopped, every frame of it rendered in the plate's set and light: the
 * shadow it throws on the dial, multiplying it, and the hand itself over that. Like a quartz watch's, the running
 * seconds step once a second, on the second.
 */
export const WatchHands = ({ plate, em, className, style }: WatchHandsProps) => {
  const canvas = useRef<HTMLCanvasElement>(null)
  const dial = DIALS[plate]

  useEffect(() => {
    const board = canvas.current
    const context = board?.getContext('2d')
    if (!board || !context || !dial) return
    const scale = window.devicePixelRatio || 1
    board.width = Math.round(dial.dial[2] * em * scale)
    board.height = Math.round(dial.dial[3] * em * scale)
    const k = board.width / dial.size[0]
    // The shadows are gathered on a sheet of their own first: where two fall on the same place the lamp is blocked
    // once, so the deeper of them darkens the dial, not both.
    const sheet = document.createElement('canvas')
    sheet.width = board.width
    sheet.height = board.height
    const shading = sheet.getContext('2d')
    let timer = 0
    let gone = false

    Promise.all([load(`/objects/mat/desk-${plate}-dial.avif`), ...ROUND.map(([name]) => load(`/objects/mat/desk-${plate}-${name}.avif`))])
      .then(([face, ...pictures]) => {
        if (gone || !shading) return
        const draw = () => {
          const now = new Date()
          const time = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds()
          const stopped = ROUND.map(([name, period], i) => {
            const hand = dial[name]
            return { picture: pictures[i], frame: hand.frames[Math.floor(((time % period) / period) * hand.stops)], gutter: hand.gutter }
          })
          context.imageSmoothingQuality = shading.imageSmoothingQuality = 'high'
          context.globalCompositeOperation = 'source-over'
          context.clearRect(0, 0, board.width, board.height)
          context.drawImage(face, 0, 0, board.width, board.height)
          shading.globalCompositeOperation = 'source-over'
          shading.clearRect(0, 0, sheet.width, sheet.height)
          shading.globalCompositeOperation = 'darken'
          for (const { picture, frame: [x, y, w, h, dx, dy] } of stopped) shading.drawImage(picture, x, y, w, h, dx * k, dy * k, w * k, h * k)
          context.globalCompositeOperation = 'multiply'
          context.drawImage(sheet, 0, 0)
          context.globalCompositeOperation = 'source-over'
          for (const { picture, frame: [x, y, w, h, dx, dy], gutter } of stopped) {
            context.drawImage(picture, x + w + 2 * gutter, y, w, h, dx * k, dy * k, w * k, h * k)
          }
          // On to the next second, a little after it turns.
          timer = window.setTimeout(draw, 1005 - (Date.now() % 1000))
        }
        draw()
        board.dataset.ready = ''
      })
      .catch(() => {})

    return () => {
      gone = true
      window.clearTimeout(timer)
      delete board.dataset.ready
    }
  }, [plate, em, dial])

  if (!dial) return null
  return <canvas ref={canvas} aria-hidden className={cn('opacity-0 data-ready:opacity-100', className)} style={style} />
}
