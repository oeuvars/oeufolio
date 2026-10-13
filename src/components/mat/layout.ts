import type { MatLayout, PropId, Size } from '../../types'

// One unit is one em of an object at its base size: sixteen reference pixels, about six millimetres of desk.
// The reference mat is the one the objects were laid out on, at that size.
const UNIT = 16
export const REF_WIDTH = 66 * UNIT
export const REF_HEIGHT = 98 * UNIT

// Where things were put down, in units from the top left of the mat, and how far each is turned in degrees.
// Nothing is squared to anything else: a desk in use, not a knoll. Objects are at their true size beside one
// another. The name is clear of the tab that the strip before this page lays over the mat's left edge.
const STREWN: Record<PropId, [number, number, number]> = {
  name: [19.8, 11, -5],
  particulars: [48.4, 13, 4],
  record: [20.5, 32.6, -7],
  recorder: [54.5, 39.5, -3],
  earpods: [40.5, 49, -8],
  ticket: [13.8, 58, 8],
  'pick-fin': [26.5, 66.5, 24],
  'pick-wedge': [28.7, 69.1, -38],
  wallet: [53, 68, 6],
  proraso: [22, 81, -12],
  razor: [44.5, 89, 8],
}

const STACK_ORDER: PropId[] = [
  'name',
  'particulars',
  'proraso',
  'razor',
  'record',
  'earpods',
  'recorder',
  'ticket',
  'wallet',
  'pick-fin',
  'pick-wedge',
]

/** The objects as they were put down, spread over a mat that wide and that tall. */
export function strewn(width: number, height: number): MatLayout {
  const layout: MatLayout = {}
  for (const id of Object.keys(STREWN) as PropId[]) {
    const [x, y, r] = STREWN[id]
    layout[id] = { x: ((x * UNIT) / REF_WIDTH) * width, y: ((y * UNIT) / REF_HEIGHT) * height, r }
  }
  return layout
}

/** Narrow mats: pack the objects into centred rows, top to bottom. */
export function stacked(sizes: Map<PropId, Size>, width: number, gap: number, top: number) {
  const layout: MatLayout = {}
  const limit = width - gap * 2
  let y = top
  let row: PropId[] = []
  let rowWidth = 0

  const flush = () => {
    if (row.length === 0) return
    const rowHeight = Math.max(...row.map((id) => sizes.get(id)!.h))
    let x = (width - rowWidth) / 2
    for (const id of row) {
      const size = sizes.get(id)!
      layout[id] = { x: x + size.w / 2, y: y + rowHeight / 2, r: 0 }
      x += size.w + gap
    }
    y += rowHeight + gap
    row = []
    rowWidth = 0
  }

  for (const id of STACK_ORDER) {
    const size = sizes.get(id)
    if (!size) continue
    if (row.length > 0 && rowWidth + gap + size.w > limit) flush()
    rowWidth += (row.length > 0 ? gap : 0) + size.w
    row.push(id)
  }
  flush()
  return { layout, height: y }
}

export function mulberry(seed: number) {
  let state = seed >>> 0
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let t = state
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
