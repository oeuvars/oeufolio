import { useEffect, useRef, useState } from 'react'

import { CatRig } from '../lib/cat-rig'
import { RIGS } from './resume-cats'

type ResumeCatProps = {
  src: string
  style: React.CSSProperties
}

const CLASS = 'pointer-events-none absolute max-w-none select-none'

/** The cut-out's name, from where cats.py writes it. */
const named = (src: string) => src.match(/resume-cat-(\w+)\./)?.[1] ?? ''

/**
 * One of the desk's cats. With a rig (resume-cats.ts) and motion allowed, its picture is drawn on a canvas that
 * bends it as the cat breathes and moves; the still picture shows until the first frame is drawn, and stays where
 * the browser cannot draw it.
 */
export const ResumeCat = ({ src, style }: ResumeCatProps) => {
  const canvas = useRef<HTMLCanvasElement>(null)
  const [live, setLive] = useState(false)
  const name = named(src)
  const rig = RIGS[name]

  useEffect(() => {
    const board = canvas.current
    if (!board || !rig || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let cat: CatRig | null = null
    let gone = false
    const picture = new Image()
    picture.src = src
    picture
      .decode()
      .then(() => {
        if (gone) return
        // Each cat keeps to its own habits: seeded by its name.
        const seed = [...name].reduce((sum, letter) => sum * 31 + letter.charCodeAt(0), 7)
        cat = CatRig.create(board, picture, rig, seed)
        cat?.start(() => setLive(true))
      })
      .catch(() => {})
    return () => {
      gone = true
      cat?.dispose()
      setLive(false)
    }
  }, [src, name, rig])

  return (
    <>
      <img alt="" src={src} draggable={false} className={CLASS} style={{ ...style, visibility: live ? 'hidden' : undefined }} />
      {rig && <canvas ref={canvas} aria-hidden data-cat={name} className={CLASS} style={style} />}
    </>
  )
}
