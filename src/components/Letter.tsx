import type { Letter as LetterData } from '../types'

type LetterProps = {
  letter: LetterData
}

/** The image's size in pixels. It is twice the size the card is meant to be read at. */
const WIDTH = 1506
const HEIGHT = 2148

/**
 * The letter (studio/letter.py) lying on its page. It is a photograph of a card, so what it says is in
 * its alt. It is never shown wider than it was written, and on a narrow page it is a good deal smaller,
 * so it opens on its own at full size.
 */
export function Letter({ letter }: LetterProps) {
  return (
    <a
      href={letter.src}
      target="_blank"
      rel="noreferrer"
      aria-label="Open the letter at full size"
      className="mx-auto block cursor-zoom-in"
      style={{ maxWidth: WIDTH / 2 }}
    >
      <img
        src={letter.src}
        alt={letter.alt}
        width={WIDTH}
        height={HEIGHT}
        draggable={false}
        className="h-auto w-full select-none [filter:drop-shadow(0_10px_14px_rgb(0_0_0/0.3))]"
      />
    </a>
  )
}
