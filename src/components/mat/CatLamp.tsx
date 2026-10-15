import { useSyncExternalStore } from 'react'

import { PROP } from './classes'
import { lamp } from './lamp'

/**
 * The desk lamp: a glazed porcelain cat in a play bow, its tail arching over its back to hold an orange dome
 * lamp head (studio/desk/objects/catlamp.py). It is in the plate, lit and unlit, and its light is in the plate
 * too. Clicking it switches it.
 */
export function CatLamp() {
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)

  return (
    <button
      type="button"
      data-prop="catlamp"
      aria-label="Lamp"
      aria-pressed={lit}
      // The lamp stands up off the desk, so the camera shows its head beyond its feet: the box reaches up to it.
      className={`${PROP} z-2 [--k:0.7] -mt-[4em] h-[22em] w-[27em] cursor-pointer touch-manipulation rounded-[5em]`}
      onClick={lamp.pull}
    />
  )
}
