import { useEffect, useState } from 'react'

import { Quill } from './Quill'
import { SmoothCursor } from './ui/smooth-cursor'

export function QuillCursor() {
  const [active, setActive] = useState(false)

  useEffect(() => {
    const onMove = (event: PointerEvent) => {
      if (event.pointerType !== 'touch') setActive(true)
    }
    window.addEventListener('pointermove', onMove, { once: true })
    return () => window.removeEventListener('pointermove', onMove)
  }, [])

  return active ? <SmoothCursor cursor={<Quill />} /> : null
}
