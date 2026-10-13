type MirrorProps = {
  children: React.ReactNode
  /** The frame's width. Its middle is the axis. */
  width?: number
}

/** Draws its children, and then again reflected about the frame's middle, as these scenes are symmetrical. */
export function Mirror({ children, width = 1200 }: MirrorProps) {
  return (
    <>
      {children}
      <g transform={`translate(${width} 0) scale(-1 1)`}>{children}</g>
    </>
  )
}
