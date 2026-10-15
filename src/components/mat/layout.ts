import type { Plate, PlateId } from '../../types'
import desk from './desk.json'

/** The rendered plates of the desk. studio/desk/desk.py renders them from the same file. */
export const PLATES = desk as unknown as Record<PlateId, Plate>
