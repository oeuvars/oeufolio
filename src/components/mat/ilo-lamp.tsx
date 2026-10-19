import { useSyncExternalStore } from 'react'

import { PROP } from './classes'
import { lamp } from './lamp'

/**
 * The desk lamp: the ILO Light, a ring of glossy cream opal glass resting on an oxblood dock
 * (studio/desk/objects/ilolamp.py). Its picture, from a camera of its own straight over it, lies over the plate,
 * lit and unlit, and its light is in the plate. The button covers the ring. Clicking it switches it.
 */
export const IloLamp = () => {
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)

  return (
    <button
      type="button"
      data-prop="ilolamp"
      aria-label="Lamp"
      aria-pressed={lit}
      // Mat lays it over the lamp in its picture, as large: --w and --h in pixels.
      className={`${PROP} z-2 h-[calc(var(--h)*1px)] w-[calc(var(--w)*1px)] cursor-pointer touch-manipulation rounded-full`}
      onClick={lamp.pull}
    />
  )
}
