import { useSyncExternalStore } from 'react'

import { PROP } from './classes'
import { lamp } from './lamp'

/**
 * The desk lamp: a glazed porcelain cat in a play bow, its tail curled up beside it and ending in a rounded tip
 * of opal glass with the lamp inside (studio/desk/objects/catlamp.py). It is in the plate, lit and unlit, and
 * its light is in the plate too. Clicking it switches it.
 */
export function CatLamp() {
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)

  return (
    <button
      type="button"
      data-prop="catlamp"
      aria-label="Lamp"
      aria-pressed={lit}
      className={`${PROP} z-2 h-[15em] w-[26em] cursor-pointer touch-manipulation rounded-[4em]`}
      onClick={lamp.pull}
    />
  )
}
