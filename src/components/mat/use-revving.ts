import { useEffect, useRef } from 'react'

/**
 * A turning part keeps its angle while its speed changes. CSS eases --rate when the part is set going and
 * when it is let go, and this hands each step of it to the part's turn animation. Returns the part's ref.
 */
export const useRevving = <T extends HTMLElement>() => {
  const part = useRef<T>(null)

  useEffect(() => {
    const el = part.current
    if (!el) return
    let frame = 0
    const follow = () => {
      const running = el.getAnimations()
      const turn = running.find((animation) => animation instanceof CSSAnimation)
      if (turn) turn.playbackRate = Number(getComputedStyle(el).getPropertyValue('--rate'))
      const easing = running.some((animation) => animation instanceof CSSTransition && animation.transitionProperty === '--rate')
      frame = easing ? requestAnimationFrame(follow) : 0
    }
    const onRun = (event: TransitionEvent) => {
      if (event.propertyName === '--rate' && !frame) follow()
    }

    el.addEventListener('transitionrun', onRun)
    follow()
    return () => {
      cancelAnimationFrame(frame)
      el.removeEventListener('transitionrun', onRun)
    }
  }, [])

  return part
}
