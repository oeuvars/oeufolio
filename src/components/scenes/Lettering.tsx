type LetteringProps = {
  x: number
  y: number
  text: string
  /** The room the line has, and the size it is set at when it fits. */
  width: number
  max: number
  /** Letterspacing, in ems. */
  tracking: number
  fill: string
  weight?: number
}

/** A capital in the wide face is about this much of an em across. */
const CAP = 0.7

/** A line of signwriting, centred on x in spaced capitals, and set smaller if it would not fit its board. */
export function Lettering({ x, y, text, width, max, tracking, fill, weight = 700 }: LetteringProps) {
  const size = Math.min(max, width / (text.length * (CAP + tracking)))

  return (
    <text
      // The spacing after the last letter is not part of the word, so the line is moved over by half of it.
      x={x + (tracking * size) / 2}
      y={y}
      textAnchor="middle"
      fontSize={size}
      fontWeight={weight}
      letterSpacing={`${tracking}em`}
      fill={fill}
      className="font-futura"
    >
      {text.toUpperCase()}
    </text>
  )
}
