import { useRef, useState } from 'react'

import type { Like } from '../../types'
import { PROP, RENDER } from './classes'
import lean from './lean.json'
import { playTape } from './tape'
import { useRevving } from './use-revving'

type RecorderProps = {
  like: Like
}

/**
 * The industrial design like: a Teenage Engineering TP-7, rendered from a model of its front. The title is
 * the readout on its display, in the plate. Over the plate lie three layers: the line
 * across the reel, the raised hub, and the marks on the hub. The line and the marks turn; the hub, which shows
 * its side and throws its shadow, stays put between them. Nothing moves
 * under the pointer. Pressing it plays a few bars off tape, and the reel turns for as long as they last,
 * then runs down.
 */
// Where studio/desk/desk.py found the lens shows each layer, against where the recorder lies: a shift in em of the
// recorder and a scale.
type Lean = { wide: number[]; tall: number[] }

type LayerProps = {
  lean: Lean
  render: string
  turning?: React.Ref<HTMLSpanElement>
}

// Each layer stands off the mat, so the lens shows it a little out from where it lies and a little larger.
const Layer = ({ lean, render, turning }: LayerProps) => {
  return (
    <span
      aria-hidden
      className="absolute top-[1.44em] left-[0.445em] aspect-square w-[10.88em] [--lean:var(--lean-wide)] group-data-[plate=tall]/mat:[--lean:var(--lean-tall)]"
      style={
        {
          '--lean-wide': `translate(${lean.wide[0]}em, ${lean.wide[1]}em) scale(${lean.wide[2]})`,
          '--lean-tall': `translate(${lean.tall[0]}em, ${lean.tall[1]}em) scale(${lean.tall[2]})`,
          // The render is already turned as the recorder lies, so it is turned back by as much as the recorder is.
          transform: 'var(--lean) rotate(calc(var(--r, 0) * -1deg))',
        } as React.CSSProperties
      }
    >
      <span
        ref={turning}
        className={turning ? 'absolute inset-0 animate-reel revving [--rate:0] group-data-[playing=true]/recorder:[--rate:3]' : 'absolute inset-0'}
      >
        <i className={`${RENDER} absolute inset-0 ${render}`} />
      </span>
    </span>
  )
}

export const Recorder = ({ like }: RecorderProps) => {
  const [playing, setPlaying] = useState(false)
  const pressedAt = useRef({ x: 0, y: 0 })
  const reel = useRevving<HTMLSpanElement>()
  const marks = useRevving<HTMLSpanElement>()

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
      <Layer
        lean={{ wide: lean.wide.reel, tall: lean.tall.reel }}
        turning={reel}
        render="bg-[url(/objects/mat/desk-wide-reel.avif)] group-data-[plate=tall]/mat:bg-[url(/objects/mat/desk-tall-reel.avif)]"
      />
      <Layer
        lean={{ wide: lean.wide.hub, tall: lean.tall.hub }}
        render="bg-[url(/objects/mat/desk-wide-hub.avif)] group-data-[plate=tall]/mat:bg-[url(/objects/mat/desk-tall-hub.avif)]"
      />
      <Layer
        lean={{ wide: lean.wide.marks, tall: lean.tall.marks }}
        turning={marks}
        render="bg-[url(/objects/mat/desk-wide-marks.avif)] group-data-[plate=tall]/mat:bg-[url(/objects/mat/desk-tall-marks.avif)]"
      />
      <h2 className="sr-only">
        {like.subject}: {like.title}
      </h2>
      <p className="sr-only">{like.note}</p>
    </article>
  )
}
