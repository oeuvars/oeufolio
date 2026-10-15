import type { Letter as LetterData } from '../types'

type LetterProps = {
  letter: LetterData
}

/** The image's size in pixels. */
const WIDTH = 1394
const HEIGHT = 2223

/**
 * The letter (studio/letter.py), written straight onto its page. It is the ink of a photographed card and
 * nothing under it, so the page shows through, and what it says is in its alt. It is as wide as the page,
 * or smaller if that is what it takes for the whole of it to show at once: the page's own margins above
 * and below are given over to it. On a narrow page it is small, so it opens on its own at full size.
 */
export function Letter({ letter }: LetterProps) {
  return (
    <a
      href={letter.src}
      target="_blank"
      rel="noreferrer"
      aria-label="Open the letter at full size"
      className="-my-[4vh] flex cursor-zoom-in justify-center"
    >
      <img
        src={letter.src}
        alt={letter.alt}
        width={WIDTH}
        height={HEIGHT}
        draggable={false}
        className="h-auto max-h-[88.8vh] w-auto max-w-full select-none"
      />
    </a>
  )
}
