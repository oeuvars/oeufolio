/**
 * Draws a picture on a canvas, `across` CSS pixels wide, at as many pixels as the screen shows it with and no more
 * than the picture has. A large picture laid as an image or a background is decoded whole, and the browser lets it go
 * again as soon as the pictures it has decoded outgrow what it keeps, as they do while a strip slides with the work
 * page's poster in it; then every repaint decodes it afresh, a frame's work many times over. A canvas keeps what is
 * drawn on it.
 */
export const paint = async (canvas: HTMLCanvasElement, src: string, across: number, signal: AbortSignal) => {
  const whole = await createImageBitmap(await (await fetch(src, { signal })).blob())
  const fine = Math.min(1, (across * (window.devicePixelRatio || 1)) / whole.width)
  const map =
    fine < 1
      ? await createImageBitmap(whole, { resizeWidth: Math.round(whole.width * fine), resizeHeight: Math.round(whole.height * fine), resizeQuality: 'high' })
      : whole
  if (!signal.aborted) {
    canvas.width = map.width
    canvas.height = map.height
    canvas.getContext('2d')?.drawImage(map, 0, 0)
  }
  whole.close()
  map.close()
  if (signal.aborted) throw signal.reason
}
