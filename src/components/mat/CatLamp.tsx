import { useSyncExternalStore } from 'react'

import { PROP } from './classes'
import { lamp } from './lamp'

/**
 * The desk lamp: a glazed porcelain cat in a play bow, her tail arching over her back to hold a bulb in a white
 * socket (studio/desk/objects/catlamp.py). Her picture, from a low camera of its own, lies over the plate, lit and
 * unlit, and her light is in the plate. The button covers her picture. Clicking it switches her.
 */
export function CatLamp() {
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)

  return (
    <button
      type="button"
      data-prop="catlamp"
      aria-label="Lamp"
      aria-pressed={lit}
      // Mat lays it over her in her picture, as large: --w and --h in pixels.
      className={`${PROP} z-2 h-[calc(var(--h)*1px)] w-[calc(var(--w)*1px)] cursor-pointer touch-manipulation rounded-[5em]`}
      onClick={lamp.pull}
    />
  )
}
