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
  private readonly width: number
  private readonly height: number

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
    this.width = width
    this.height = height
    this.skin = new Skin(rig, width, height)
    this.behaviour = new Behaviour(rig, seed, () => this.skin.blank())
    this.pose = this.skin.blank()
    painter.load(picture, width, height, this.skin.uv, this.skin.indices)
  }

  /** Starts the cat moving; `shown` is called once its first frame is on the canvas. */
  start(shown: () => void) {
    let first = true
    const tick = (time: number) => {
      // As many pixels as the screen gives its box, zoomed in or pinched in or not, so it stays as sharp as the
      // still picture; and no more than the picture has, which the browser then scales as it scales the still.
      const box = this.canvas.getBoundingClientRect()
      const ratio = (window.devicePixelRatio || 1) * (window.visualViewport?.scale ?? 1)
      const fit = Math.min(1, (box.width * ratio) / this.width)
      this.painter.fit(Math.round(this.width * fit), Math.round(this.height * fit))
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
