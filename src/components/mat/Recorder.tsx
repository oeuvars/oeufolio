import { useRef, useState } from 'react'

import type { Like } from '../../types'
import { PROP, RENDER, SKIN } from './classes'
import { playTape } from './tape'
import { useRevving } from './useRevving'

type RecorderProps = {
  like: Like
}

/**
 * The industrial design like: a Teenage Engineering TP-7, rendered from a model of its front. The title is
 * the readout on its display, in the render. The reel's hub is its own render so it can turn. Nothing moves
 * under the pointer. Pressing it plays a few bars off tape, and the reel turns for as long as they last,
 * then runs down.
 */
export function Recorder({ like }: RecorderProps) {
  const [playing, setPlaying] = useState(false)
  const pressedAt = useRef({ x: 0, y: 0 })
  const reel = useRevving<HTMLElement>()

  const play = (event: React.MouseEvent) => {
    // Carrying it across the mat is not pressing play.
    if (playing || Math.hypot(event.clientX - pressedAt.current.x, event.clientY - pressedAt.current.y) > 6) return
    setPlaying(true)
    window.setTimeout(() => setPlaying(false), playTape() * 1000)
  }

  return (
    <article
      data-prop="recorder"
      data-playing={playing}
      className={`${PROP} group/recorder z-2 h-[17em] w-[11.875em] [--bleed:3] [--tall:1.4]`}
      onPointerDown={(event) => (pressedAt.current = { x: event.clientX, y: event.clientY })}
      onClick={play}
    >
      <i aria-hidden className={`${SKIN} bg-[url(/objects/mat/recorder.avif)]`} />
      <i
        ref={reel}
        aria-hidden
        className={`${RENDER} absolute top-[1.44em] left-[0.445em] aspect-square w-[10.88em] animate-reel revving bg-[url(/objects/mat/reel.avif)] [--rate:0] group-data-[playing=true]/recorder:[--rate:3]`}
      />
      <h2 className="sr-only">
        {like.subject}: {like.title}
      </h2>
      <p className="sr-only">{like.note}</p>
    </article>
  )
}
