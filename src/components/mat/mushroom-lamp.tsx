import { useSyncExternalStore } from 'react'

import { PROP } from './classes'
import { lamp } from './lamp'

/**
 * The desk lamp: a mushroom lamp in deep oxblood lacquer, its domed shade over a tapering stem, an opal ring under
 * the shade giving a soft yellow light (studio/desk/objects/mushroomlamp.py). Its picture, from a camera of its own
 * straight over it, lies over the plate, lit and unlit, and its light is in the plate. The button covers the shade.
 * Clicking it switches it.
 */
export function MushroomLamp() {
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)

  return (
    <button
      type="button"
      data-prop="mushroomlamp"
      aria-label="Lamp"
      aria-pressed={lit}
      // Mat lays it over the shade in its picture, as large: --w and --h in pixels.
      className={`${PROP} z-2 h-[calc(var(--h)*1px)] w-[calc(var(--w)*1px)] cursor-pointer touch-manipulation rounded-full`}
      onClick={lamp.pull}
    />
  )
}
