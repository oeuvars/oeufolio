import type { Plate, PlateId } from '../../types'
import desk from './desk.json'

/** The rendered plates of the desk. studio/desk/desk.py renders them from the same file. */
export const PLATES = desk as unknown as Record<PlateId, Plate>

// The bulb in the lamp's own box, in em of the lamp.
export const BULB = { x: 4.5, y: 9.874 }
