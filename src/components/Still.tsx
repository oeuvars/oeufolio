import type { Signage } from '../types'
import { Archive } from './scenes/Archive'
import { FrontDesk } from './scenes/FrontDesk'
import { Office } from './scenes/Office'

type StillProps = Signage & {
  /** Which room: they are dealt out in order, and come round again. */
  index: number
}

const rooms = [Office, FrontDesk, Archive]

/** A furnished room of the building, with the words it is given lettered on its sign. */
export function Still({ index, sign }: StillProps) {
  const Room = rooms[index % rooms.length]

  return <Room sign={sign} />
}
