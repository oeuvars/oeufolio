/**
 * The work page's poster folded into its strip (studio/poster recut): the poster recut down the strip, its windows set
 * off a grid at different sizes and the sign's two words hung down among them. There is no wall in it, so the strip's
 * paper shows between them. It is light printed on that paper, as the page is, so it is laid over the paper as a
 * screen. It fades into the poster as the strip opens, and back as it folds (Fold).
 */
export const StripPoster = () => (
  // Half a tear in from either side, past where the strip before it bites in, and fitted whole, so no window is cut.
  <div aria-hidden className="absolute inset-y-0 inset-x-2 mix-blend-screen">
    <img src="/objects/poster-strip.avif" alt="" draggable={false} className="size-full max-w-none object-contain select-none" />
  </div>
)
