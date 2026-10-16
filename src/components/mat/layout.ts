import type { Plate, PlateId, Portraits } from '../../types'
import desk from './desk.json'
import portrait from './portrait.json'

/** The rendered plates of the desk. studio/desk/desk.py renders them from the same file. */
export const PLATES = desk as unknown as Record<PlateId, Plate>

/** Where on each plate the props seen from a camera of their own lie: studio/desk/desk.py writes it. */
export const PORTRAITS = portrait as unknown as Record<PlateId, Portraits>
