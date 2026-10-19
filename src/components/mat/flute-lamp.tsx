import { useSyncExternalStore } from 'react'

import { PROP } from './classes'
import { lamp } from './lamp'

/**
 * The desk lamp: a round light of fluted amber glass under a copper mirror coat, on a white back, lying face up
 * (studio/desk/objects/flutelamp.py). Its picture, from a camera of its own straight over it, lies over the plate,
 * lit and unlit, and its light is in the plate. The button covers the glass. Clicking it switches it.
 */
export const FluteLamp = () => {
  const lit = useSyncExternalStore(lamp.subscribe, lamp.isOn, lamp.isOn)

  return (
    <button
      type="button"
      data-prop="flutelamp"
      aria-label="Lamp"
      aria-pressed={lit}
      // Mat lays it over the glass in its picture, as large: --w and --h in pixels.
      className={`${PROP} z-2 h-[calc(var(--h)*1px)] w-[calc(var(--w)*1px)] cursor-pointer touch-manipulation rounded-full`}
      onClick={lamp.pull}
    />
  )
}
