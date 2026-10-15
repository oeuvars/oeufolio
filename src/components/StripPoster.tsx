/**
 * The work page's poster folded into its strip (studio/poster): the middle column of its windows, the full height
 * of it, with the sign's light running in from either side but none of the passages, which come with the page.
 * Like the building, it has no frame, so it runs on under the tab to the strip's edge.
 */
export function StripPoster() {
  return (
    <img
      aria-hidden
      src="/objects/poster-strip.avif"
      alt=""
      className="absolute inset-y-0 left-0 h-full w-full max-w-none object-cover object-center"
    />
  )
}
