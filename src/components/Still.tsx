import type { Room, Signage } from '../types'
import { Bank } from './scenes/Bank'
import { Dock } from './scenes/Dock'
import { Warehouse } from './scenes/Warehouse'

type StillProps = Signage & {
  room: Room
}

const rooms = { warehouse: Warehouse, bank: Bank, dock: Dock }

/** A furnished room of the building, with the words it is given lettered on its sign. */
export function Still({ room, sign }: StillProps) {
  const Scene = rooms[room]

  return <Scene sign={sign} />
}
