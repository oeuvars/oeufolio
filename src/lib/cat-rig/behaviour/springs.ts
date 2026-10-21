import type { Pose, Rig } from '../types'

// The longest step a spring is moved in at once, in seconds, so the stiffest stay steady.
const STEP = 1 / 240

type Sprung = {
  name: string
  // Each bone's direction from the root (not its turn from the bone before it), so a looser tip lags the root.
  rate: Float64Array
  damping: Float64Array
  angle: Float64Array
  speed: Float64Array
  shift: Float64Array
  drift: Float64Array
}

/**
 * Where each part is, chasing where the cat means it to be. A spring carries every bone and shift there, quickly at
 * first and settling slowly, as a cat's head does when it turns; down a tail the springs loosen, so the tip trails
 * the root and swings through after it stops.
 */
export class Springs {
  private readonly parts: Sprung[] = []

  constructor(rig: Rig) {
    for (const [name, part] of Object.entries(rig.parts)) {
      if (part.kind !== 'chain') continue
      const bones = part.joints.length - 1
      const { rate, damping, tip = { rate, damping } } = part.spring
      const along = (b: number) => (bones > 1 ? b / (bones - 1) : 0)
      this.parts.push({
        name,
        rate: Float64Array.from({ length: bones }, (_, b) => rate + (tip.rate - rate) * along(b)),
        damping: Float64Array.from({ length: bones }, (_, b) => damping + (tip.damping - damping) * along(b)),
        angle: new Float64Array(bones),
        speed: new Float64Array(bones),
        shift: new Float64Array(2),
        drift: new Float64Array(2),
      })
    }
  }

  /** Moves every spring on by `seconds` toward `target`, and writes where they are into `pose`. */
  step(target: Pose, seconds: number, pose: Pose) {
    const steps = Math.max(1, Math.ceil(seconds / STEP))
    const dt = seconds / steps
    for (const part of this.parts) {
      const goal = target[part.name]
      const out = pose[part.name]
      const { rate, damping, angle, speed, shift, drift } = part
      for (let s = 0; s < steps; s++) {
        let toward = 0
        for (let b = 0; b < angle.length; b++) {
          toward += goal.angles[b]
          const w = rate[b]
          speed[b] += (w * w * (toward - angle[b]) - 2 * damping[b] * w * speed[b]) * dt
          angle[b] += speed[b] * dt
        }
        for (let k = 0; k < 2; k++) {
          const w = rate[0]
          drift[k] += (w * w * (goal.shift[k] - shift[k]) - 2 * damping[0] * w * drift[k]) * dt
          shift[k] += drift[k] * dt
        }
      }
      for (let b = 0; b < angle.length; b++) out.angles[b] = angle[b] - (b ? angle[b - 1] : 0)
      out.shift[0] = shift[0]
      out.shift[1] = shift[1]
    }
  }
}
