import { useRef, useState } from 'react'

import type { Like } from '../../types'
import { PROP, RENDER } from './classes'
import { playTape } from './tape'
import { useRevving } from './useRevving'

type RecorderProps = {
  like: Like
}

/**
 * The industrial design like: a Teenage Engineering TP-7, rendered from a model of its front. The title is
 * the readout on its display, in the plate. The reel's hub is a layer of its own, by day and by the lamp, so
 * it can turn. Nothing moves
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
      className={`${PROP} group/recorder z-2 h-[17em] w-[11.875em] cursor-pointer`}
      onPointerDown={(event) => (pressedAt.current = { x: event.clientX, y: event.clientY })}
      onClick={play}
    >
      <span
        ref={reel}
        aria-hidden
        className="absolute top-[1.44em] left-[0.445em] aspect-square w-[10.88em] animate-reel revving [--rate:0] group-data-[playing=true]/recorder:[--rate:3]"
      >
        <i className={`${RENDER} absolute inset-0 bg-[url(/objects/mat/desk-wide-reel.avif)] opacity-[calc(1-var(--lamp))] group-data-[plate=tall]/mat:bg-[url(/objects/mat/desk-tall-reel.avif)]`} />
        <i className={`${RENDER} absolute inset-0 bg-[url(/objects/mat/desk-wide-reel-lamp.avif)] opacity-[var(--lamp)] group-data-[plate=tall]/mat:bg-[url(/objects/mat/desk-tall-reel-lamp.avif)]`} />
      </span>
      <h2 className="sr-only">
        {like.subject}: {like.title}
      </h2>
      <p className="sr-only">{like.note}</p>
    </article>
  )
}
