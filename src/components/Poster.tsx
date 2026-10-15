import { POSTER } from './house'
import { Reveal } from './Reveal'

/**
 * The work page: a poster of lit windows in a block of flats at night (studio/poster), with "human
 * experience" glowing across them and passages set between them. Its type is in the picture, not over it. It
 * stands the panel's height, and the strip opens no wider than it (SiteShell), on the poster's own dark, its edges
 * fading into it.
 */
export function Poster() {
  return (
    <div className="absolute inset-0 flex items-center justify-center overflow-hidden bg-[#100e0c]">
      <h2 className="sr-only">Experience</h2>
      <Reveal delay={0.3} className="flex size-full items-center justify-center">
        <img
          src="/objects/poster.avif"
          alt="A poster of a block of flats at night, its lit windows each a different room with someone in silhouette: a saxophonist, a woman at a candle, two women at a yellow window, a child at a lilac curtain. The words human experience glow across it, and four italic passages are set between the windows."
          width={POSTER.width}
          height={POSTER.height}
          draggable={false}
          className="block h-auto max-h-full w-auto max-w-full select-none [mask-composite:intersect] [mask-image:linear-gradient(to_right,transparent,#000_7%,#000_93%,transparent),linear-gradient(to_bottom,transparent,#000_5%,#000_95%,transparent)]"
        />
      </Reveal>
    </div>
  )
}
