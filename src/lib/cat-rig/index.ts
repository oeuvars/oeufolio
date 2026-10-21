import { Behaviour } from './behaviour'
import { Painter } from './painter'
import { Skin } from './skin'
import type { Rig } from './types'

/**
 * A cat cut out of a photograph, brought to life on a canvas: the picture pinned to a mesh (Skin) that bends as the
 * cat's head, tail, paws and ribs move (Behaviour), drawn each frame in WebGL (Painter).
 */
export class CatRig {
  private readonly skin: Skin
  private readonly behaviour: Behaviour
  private readonly pose
  private frame = 0

  /** The cat on the canvas, or none where the browser cannot draw it. */
  static create(canvas: HTMLCanvasElement, picture: HTMLImageElement, rig: Rig, seed: number) {
    const painter = Painter.open(canvas)
    return painter ? new CatRig(canvas, painter, picture, rig, seed) : null
  }

  private constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly painter: Painter,
    picture: HTMLImageElement,
    rig: Rig,
    seed: number,
  ) {
    const width = picture.naturalWidth
    const height = picture.naturalHeight
    this.skin = new Skin(rig, width, height)
    this.behaviour = new Behaviour(rig, seed)
    this.pose = this.skin.blank()
    painter.load(picture, width, height, this.skin.uv, this.skin.indices)
  }

  /** Starts the cat moving; `shown` is called once its first frame is on the canvas. */
  start(shown: () => void) {
    let first = true
    const tick = (time: number) => {
      // Sized to its box at the screen's pixel density every frame, so zooming keeps it sharp.
      const ratio = window.devicePixelRatio || 1
      this.painter.fit(Math.round(this.canvas.clientWidth * ratio), Math.round(this.canvas.clientHeight * ratio))
      this.behaviour.pose(time / 1000, this.pose)
      this.painter.draw(this.skin.deform(this.pose))
      if (first) {
        first = false
        shown()
      }
      this.frame = requestAnimationFrame(tick)
    }
    this.frame = requestAnimationFrame(tick)
  }

  dispose() {
    cancelAnimationFrame(this.frame)
    this.painter.dispose()
  }
}
