import { POSTER } from './house'
import { Reveal } from './Reveal'

/**
 * The work page: a poster of lit windows in a block of flats at night (studio/poster), with "human
 * experience" glowing across them and passages set between them. Its type is in the picture, not over it. It
 * is printed on the page's own paper: the strip, its tab and the wall round the windows are all one material, the
 * poster's bare wall as a tile (SiteShell), and the picture is only the light on it, laid over the paper as a screen,
 * so where it is dark the paper shows. It covers the strip out to its torn edge; the strip opens only as wide as the
 * poster is at the window's height (SiteShell), so almost none of it is cropped. On a phone the strip is far narrower
 * than the poster, so it runs the strip's width instead, with the paper above and below it.
 */
export function Poster() {
  return (
    <div className="absolute inset-0 flex items-center overflow-hidden mix-blend-screen">
      <h2 className="sr-only">Experience</h2>
      <Reveal delay={0.3} className="w-full md:size-full">
        <img
          src="/objects/poster.avif"
          alt="A poster of a block of flats at night, its lit windows each a different room with someone in silhouette: a saxophonist, a woman at a candle, two women at a yellow window, a child at a lilac curtain. The words human experience glow across it, and four italic passages are set between the windows."
          width={POSTER.width}
          height={POSTER.height}
          draggable={false}
          className="block h-auto w-full select-none [mask-image:linear-gradient(to_bottom,transparent,#000_6%,#000_94%,transparent)] md:size-full md:object-cover md:[mask-image:none]"
        />
      </Reveal>
    </div>
  )
}
