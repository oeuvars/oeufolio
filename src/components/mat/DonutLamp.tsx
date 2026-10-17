import { useSyncExternalStore } from 'react'

import { PROP } from './classes'
import { lamp } from './lamp'

/**
 * The desk lamp: a donut of blown orange opal glass lying on the mat, lit from inside
 * (studio/desk/objects/donutlamp.py). It is in the plate, lit and unlit, and so is its light on everything round
 * it. The button covers the glass, a little up the page, where the lens shows its top. Clicking it switches it.
 */
export function DonutLamp() {
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)

  return (
    <button
      type="button"
      data-prop="donutlamp"
      aria-label="Lamp"
      aria-pressed={lit}
      className={`${PROP} z-2 -mt-[1.5em] size-[15em] cursor-pointer touch-manipulation rounded-full`}
      onClick={lamp.pull}
    />
  )
}
