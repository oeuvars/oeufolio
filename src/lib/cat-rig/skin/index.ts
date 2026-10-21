import type { Chain, Pose, Rig, Swell } from '../types'

// Pixels of the picture between one point of the mesh and the next: two thirds of a CSS pixel on the desk.
const STEP = 4
const RADIANS = Math.PI / 180

type BoundChain = {
  name: string
  joints: Float32Array
  /** The vertices the chain holds, how firmly, and the two bones each follows, the first by `share`. */
  vertices: Uint32Array
  weights: Float32Array
  first: Uint8Array
  second: Uint8Array
  share: Float32Array
  // This frame's bones, worked out once for all the vertices: where each joint has gone and how far its bone turns.
  moved: Float32Array
  cos: Float32Array
  sin: Float32Array
}

type BoundSwell = {
  name: string
  centre: [number, number]
  /** The way the ribs widen, as a unit vector. */
  across: [number, number]
  vertices: Uint32Array
  weights: Float32Array
}

const smooth = (from: number, to: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - from) / (to - from)))
  return t * t * (3 - 2 * t)
}

/** How far p is from the bone a to b, and how far along it its nearest point lies (0 at a, 1 at b). */
const near = (px: number, py: number, ax: number, ay: number, bx: number, by: number) => {
  const dx = bx - ax
  const dy = by - ay
  const along = Math.min(1, Math.max(0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
  return { distance: Math.hypot(px - ax - along * dx, py - ay - along * dy), along }
}

/**
 * The cut-out as a fine mesh laid over its picture, each point of it bound to the parts that hold it. Each frame the
 * points move as their parts' bones do, and the picture, pinned to them, bends with them: the photograph's own fur
 * moves, nothing is drawn over it. Where a tail swings off the desk, the desk it lay on shows, as it would.
 */
export class Skin {
  readonly rest: Float32Array
  readonly uv: Float32Array
  readonly indices: Uint32Array
  readonly positions: Float32Array
  private readonly chains: BoundChain[] = []
  private readonly swells: BoundSwell[] = []

  constructor(
    private readonly rig: Rig,
    readonly width: number,
    readonly height: number,
  ) {
    const columns = Math.ceil(width / STEP) + 1
    const rows = Math.ceil(height / STEP) + 1
    this.rest = new Float32Array(columns * rows * 2)
    this.uv = new Float32Array(columns * rows * 2)
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        const i = (row * columns + column) * 2
        const x = Math.min(column * STEP, width)
        const y = Math.min(row * STEP, height)
        this.rest[i] = x
        this.rest[i + 1] = y
        this.uv[i] = x / width
        this.uv[i + 1] = y / height
      }
    }
    this.indices = new Uint32Array((columns - 1) * (rows - 1) * 6)
    let k = 0
    for (let row = 0; row < rows - 1; row++) {
      for (let column = 0; column < columns - 1; column++) {
        const a = row * columns + column
        const b = a + 1
        const c = a + columns
        const d = c + 1
        this.indices.set([a, c, b, b, c, d], k)
        k += 6
      }
    }
    this.positions = new Float32Array(this.rest)
    this.bind()
  }

  /** A pose with every part at rest, for the behaviour to fill in each frame. */
  blank(): Pose {
    const pose: Pose = {}
    for (const [name, part] of Object.entries(this.rig.parts)) {
      pose[name] = { angles: new Array(part.kind === 'chain' ? part.joints.length - 1 : 0).fill(0), shift: [0, 0], swell: 0 }
    }
    return pose
  }

  /** Where every point of the mesh lies in this pose. */
  deform(pose: Pose) {
    const out = this.positions
    out.set(this.rest)
    const rest = this.rest
    for (const chain of this.chains) {
      const { angles, shift } = pose[chain.name]
      const { joints, moved, cos, sin } = chain
      moved[0] = joints[0] + shift[0]
      moved[1] = joints[1] + shift[1]
      let turn = 0
      for (let b = 0; b < angles.length; b++) {
        turn += angles[b] * RADIANS
        cos[b] = Math.cos(turn)
        sin[b] = Math.sin(turn)
        const dx = joints[2 * b + 2] - joints[2 * b]
        const dy = joints[2 * b + 3] - joints[2 * b + 1]
        moved[2 * b + 2] = moved[2 * b] + cos[b] * dx - sin[b] * dy
        moved[2 * b + 3] = moved[2 * b + 1] + sin[b] * dx + cos[b] * dy
      }
      for (let n = 0; n < chain.vertices.length; n++) {
        const i = chain.vertices[n] * 2
        const x = rest[i]
        const y = rest[i + 1]
        const a = chain.first[n]
        const b = chain.second[n]
        const share = chain.share[n]
        const ax = x - joints[2 * a]
        const ay = y - joints[2 * a + 1]
        const bx = x - joints[2 * b]
        const by = y - joints[2 * b + 1]
        const px = share * (moved[2 * a] + cos[a] * ax - sin[a] * ay) + (1 - share) * (moved[2 * b] + cos[b] * bx - sin[b] * by)
        const py = share * (moved[2 * a + 1] + sin[a] * ax + cos[a] * ay) + (1 - share) * (moved[2 * b + 1] + sin[b] * bx + cos[b] * by)
        out[i] += chain.weights[n] * (px - x)
        out[i + 1] += chain.weights[n] * (py - y)
      }
    }
    for (const swell of this.swells) {
      const grow = pose[swell.name].swell
      if (grow === 0) continue
      const [cx, cy] = swell.centre
      const [ux, uy] = swell.across
      for (let n = 0; n < swell.vertices.length; n++) {
        const i = swell.vertices[n] * 2
        const dx = rest[i] - cx
        const dy = rest[i + 1] - cy
        // Out along the ribs, and a quarter as much every way.
        const wide = (dx * ux + dy * uy) * 0.75
        const k = swell.weights[n] * grow
        out[i] += k * (wide * ux + 0.25 * dx)
        out[i + 1] += k * (wide * uy + 0.25 * dy)
      }
    }
    return out
  }

  /** How firmly each part holds each point of the mesh, before any part yields to another. */
  private hold(part: Chain | Swell, x: number, y: number) {
    if (part.kind === 'swell') {
      const [cx, cy] = part.centre
      const [rx, ry] = part.radii
      const e = Math.hypot((x - cx) / rx, (y - cy) / ry)
      return { weight: 1 - smooth(1, 1 + part.soft / Math.min(rx, ry), e), first: 0, second: 0, share: 1 }
    }
    const { joints, reach } = part
    // The two nearest bones, and how near the point lies to the part's outline about them.
    let best = { bone: 0, distance: Infinity, along: 0 }
    const distances: number[] = []
    for (let b = 0; b < joints.length - 1; b++) {
      const { distance, along } = near(x, y, joints[b][0], joints[b][1], joints[b + 1][0], joints[b + 1][1])
      distances.push(distance)
      if (distance < best.distance) best = { bone: b, distance, along }
    }
    const width = reach[best.bone] + (reach[best.bone + 1] - reach[best.bone]) * best.along
    const weight = 1 - smooth(width, width + part.soft, best.distance)
    if (distances.length === 1) return { weight, first: 0, second: 0, share: 1 }
    // Near a joint the point follows both bones on either side of it, so the part bends there rather than kinks.
    const length = (b: number) => Math.hypot(joints[b + 1][0] - joints[b][0], joints[b + 1][1] - joints[b][1])
    const neighbour =
      best.bone === 0 ? 1 : best.bone === distances.length - 1 ? best.bone - 1 : distances[best.bone - 1] < distances[best.bone + 1] ? best.bone - 1 : best.bone + 1
    const sigma = 0.4 * (length(best.bone) + length(neighbour)) / 2
    const own = Math.exp(-((best.distance / sigma) ** 2))
    const other = Math.exp(-((distances[neighbour] / sigma) ** 2))
    return { weight, first: best.bone, second: neighbour, share: own / (own + other) }
  }

  private bind() {
    const count = this.rest.length / 2
    const parts = Object.entries(this.rig.parts)
    const holds = parts.map(([, part]) => {
      const list = []
      for (let v = 0; v < count; v++) list.push(this.hold(part, this.rest[2 * v], this.rest[2 * v + 1]))
      return list
    })
    parts.forEach(([name, part], p) => {
      const yielded = part.kind === 'chain' ? (part.yields ?? []).map((other) => holds[parts.findIndex(([n]) => n === other)]) : []
      const kept: number[] = []
      const weights: number[] = []
      for (let v = 0; v < count; v++) {
        let weight = holds[p][v].weight
        for (const other of yielded) weight *= 1 - other[v].weight
        if (weight > 0.001) {
          kept.push(v)
          weights.push(weight)
        }
      }
      if (part.kind === 'swell') {
        const across = (part.across * Math.PI) / 180
        this.swells.push({
          name,
          centre: part.centre,
          across: [Math.cos(across), Math.sin(across)],
          vertices: Uint32Array.from(kept),
          weights: Float32Array.from(weights),
        })
        return
      }
      const bones = part.joints.length - 1
      this.chains.push({
        name,
        joints: Float32Array.from(part.joints.flat()),
        vertices: Uint32Array.from(kept),
        weights: Float32Array.from(weights),
        first: Uint8Array.from(kept.map((v) => holds[p][v].first)),
        second: Uint8Array.from(kept.map((v) => holds[p][v].second)),
        share: Float32Array.from(kept.map((v) => holds[p][v].share)),
        moved: new Float32Array(2 * (bones + 1)),
        cos: new Float32Array(bones),
        sin: new Float32Array(bones),
      })
    })
  }
}
