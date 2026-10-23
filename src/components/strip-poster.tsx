import { POSTER, POSTER_COLUMN } from './house'

/**
 * The work page's poster folded into its strip (studio/poster): the middle column of its windows, the full height
 * of it, with the sign's light running in from either side but none of the passages, which come with the page.
 * Like the building, it has no frame, so it runs on under the tab to the strip's edge. It is light printed on the
 * strip's paper, as the page is, so it is laid over the paper as a screen. Its sign and windows go to their places on
 * the poster as the strip opens, and back as it folds (Fold).
 */
export const StripPoster = () => (
  <div aria-hidden className="absolute inset-0 mix-blend-screen [container-type:size]">
    {/* The column as a picture covering the strip, centred. */}
    <div
      className="absolute top-1/2 left-1/2 h-[max(100cqh,calc(100cqw*2943/882))] -translate-x-1/2 -translate-y-1/2"
      style={{ aspectRatio: `${POSTER_COLUMN.width} / ${POSTER.height}` }}
    >
      <img src="/objects/poster-strip.avif" alt="" draggable={false} className="size-full max-w-none select-none" />
    </div>
  </div>
)
