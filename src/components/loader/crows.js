// The loader, run inline at the top of the body so it is up before the bundle, the fonts or a single picture arrive.
// Two crows flap over blue paper, set in type: the stop-motion loop of marker-drawn crows in crows.txt, set as
// characters by studio/crows/ascii.py, played at its own ten frames a second, each drawing a grid of characters in ink
// over a light grain of paper whose colour flickers from drawing to drawing as the photographs do. Once everything is
// in, the type breaks up cell by cell and the paper is lifted. A classic script, not a module: no imports, nothing
// left on window.
;(() => {
  const root = document.getElementById('loader')
  const source = document.getElementById('loader-crows')
  if (!root || !source) return

  const INK = '#10141a'
  const GRAIN = 'rgba(236,250,255,.42)'
  const FONT = 'Menlo,"SF Mono",ui-monospace,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace'
  // Menlo's width to its height, which the grids were set at; other fonts are spaced out or in to it.
  const ADVANCE = 0.602
  // Type smaller than this, in pixels, and the fine grid gives way to the coarse one.
  const SMALLEST = 7.5
  // The share of how far the crows reach over the whole loop, across and up and down, that is kept on screen.
  const REACH = 0.92
  // The paper's grain: how many cells in a hundred carry a mark, and what marks.
  const SPECKS = ".,'`:.-"
  const SPECKLED = 0.035
  // Each crow character breaks down through these to nothing on the way out, a step every so often.
  const DECAY = '%+:. '
  const STEP = 45
  const SCATTER = 420
  // A page in by this is from the cache, and the paper is lifted straight off without the crows being shown.
  const QUICK = 250
  // How long the bar takes to get most of the way when nothing is known of what is still to come, in ms.
  const PATIENCE = 9000
  // Past this the page is shown as it is, so a request that never ends cannot hold it shut.
  const GIVE_UP = 120000

  /** The loop: its frame rate, the drawing on each frame, each drawing's paper, and the grids it was set on. */
  const read = (text) => {
    const lines = text.replace(/^\n+/, '').split('\n')
    const fps = +lines[0]
    const order = lines[1].split(' ').map(Number)
    const papers = lines[2].split(' ').map((pair) => pair.split(','))
    const grids = []
    for (let i = 3; /^\d+ \d+$/.test(lines[i] || ''); ) {
      const [cols, rows] = lines[i].split(' ').map(Number)
      i++
      const drawings = []
      let x0 = cols
      let x1 = 0
      let y0 = rows
      let y1 = 0
      for (let d = 0; d < papers.length; d++, i += rows) {
        const drawing = lines.slice(i, i + rows)
        drawing.forEach((line, y) => {
          const start = line.search(/\S/)
          if (start < 0) return
          x0 = Math.min(x0, start)
          x1 = Math.max(x1, line.length)
          y0 = Math.min(y0, y)
          y1 = Math.max(y1, y + 1)
        })
        drawings.push(drawing)
      }
      grids.push({ cols, rows, drawings, box: [x0, y0, x1, y1] })
    }
    return { fps, order, papers, grids }
  }

  const random = (seed) => () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }

  /** The two crows and the paper under them, set to fill the screen. */
  class Type {
    constructor(paper, loop) {
      this.paper = paper
      this.loop = loop
      this.grain = document.createElement('pre')
      this.grain.style.color = GRAIN
      this.ink = document.createElement('pre')
      this.ink.style.color = INK
      paper.append(this.grain, this.ink)
      // How wide a character of the font that is there really is, to space it out or in to Menlo's.
      const context = document.createElement('canvas').getContext('2d')
      context.font = `100px ${FONT}`
      this.advance = context.measureText('MMMMMMMMMM').width / 1000 || ADVANCE
      this.drawing = -1
      this.lay()
    }

    /** Picks the grid and the size of type that fit the crows, as large as they go, on the screen as it is now. */
    lay() {
      const w = innerWidth
      const h = innerHeight
      const { grids } = this.loop
      let size = 0
      let grid = grids[0]
      for (grid of grids) {
        const [x0, y0, x1, y1] = grid.box
        // As large as the crows' reach over the loop, all but its tips, fits; the film crops them as closely.
        size = Math.min(w / ((x1 - x0) * ADVANCE * REACH), h / ((y1 - y0) * REACH))
        if (size >= SMALLEST) break
      }
      size = Math.floor(size * 4) / 4
      const cell = size * ADVANCE
      const cols = Math.ceil(w / cell)
      const rows = Math.ceil(h / size)
      const [x0, y0, x1, y1] = grid.box
      const left = Math.round((cols - (x0 + x1)) / 2)
      const top = Math.round((rows - (y0 + y1)) / 2)
      for (const pre of [this.grain, this.ink]) {
        pre.style.fontSize = `${size}px`
        pre.style.letterSpacing = `${(ADVANCE - this.advance) * size}px`
      }

      // Each drawing as the screen's rows, and the grain of the paper round it, set once.
      const rand = random(7)
      const specks = []
      for (let i = 0; i < cols * rows; i++) {
        // A little more grain toward the foot of the sheet, where the light falls on it.
        const y = Math.floor(i / cols) / rows
        specks.push(rand() < SPECKLED * (0.7 + 0.6 * y) ? SPECKS[Math.floor(rand() * SPECKS.length)] : ' ')
      }
      this.frames = grid.drawings.map((drawing, d) => {
        const ink = []
        const grain = []
        const shift = random(100 + d)
        for (let r = 0; r < rows; r++) {
          let line = drawing[r - top] || ''
          line = left >= 0 ? ' '.repeat(left) + line : line.slice(-left)
          line = line.slice(0, cols)
          ink.push(line.trimEnd())
          let dust = ''
          for (let c = 0; c < cols; c++) {
            // The paper was shot again for each drawing, so a few of its specks are not where they were.
            const speck = shift() < 0.2 ? (shift() < SPECKLED ? SPECKS[Math.floor(shift() * SPECKS.length)] : ' ') : specks[r * cols + c]
            dust += line[c] && line[c] !== ' ' ? ' ' : speck
          }
          grain.push(dust.trimEnd())
        }
        return { ink, grain }
      })
      this.drawing = -1
    }

    /** Shows drawing `d`. */
    show(d) {
      if (d === this.drawing) return
      this.drawing = d
      const [top, bottom] = this.loop.papers[d]
      this.paper.style.background = `linear-gradient(${top},${bottom})`
      this.ink.textContent = this.frames[d].ink.join('\n')
      this.grain.textContent = this.frames[d].grain.join('\n')
    }

    /** Breaks the type up, cell by cell, over `ms`; calls `done` when nothing is left. */
    scatter(done) {
      const { ink, grain } = this.frames[this.drawing]
      const rand = random(3)
      const lines = (rows) => rows.map((line) => [...line].map((char) => (char === ' ' ? null : { char, at: rand() * SCATTER })))
      const cells = { ink: lines(ink), grain: lines(grain) }
      const start = performance.now()
      const frame = (now) => {
        const age = now - start
        const set = (rows, decays) =>
          rows
            .map((row) =>
              row
                .map((cell) => {
                  if (!cell || age < cell.at) return cell ? cell.char : ' '
                  if (!decays) return ' '
                  return DECAY[Math.min(DECAY.length - 1, Math.floor((age - cell.at) / STEP))]
                })
                .join(''),
            )
            .join('\n')
        this.ink.textContent = set(cells.ink, true)
        this.grain.textContent = set(cells.grain, false)
        if (age < SCATTER + STEP * DECAY.length) this.frame = requestAnimationFrame(frame)
        else done()
      }
      this.frame = requestAnimationFrame(frame)
    }
  }

  /** The pictures the page has asked for and how many of them are in, by URL. */
  class Arrivals {
    constructor() {
      this.seen = new Set()
      this.done = new Set()
      this.lastDone = 0
      this.loaded = document.readyState === 'complete'
      this.loadedAt = this.loaded ? performance.now() : 0
      addEventListener('load', () => {
        this.loaded = true
        this.loadedAt = performance.now()
      })
    }

    static picture = /\.(avif|webp|png|jpe?g|gif|svg)(\?|#|$)/i

    /** The share of what the markup has asked for so far that has come in. */
    take() {
      for (const img of document.images) if (img.currentSrc || img.src) this.seen.add(new URL(img.currentSrc || img.src, location.href).href)
      for (const node of document.querySelectorAll('[style*="url("]')) {
        for (const [, src] of node.getAttribute('style').matchAll(/url\(["']?([^"')]+)["']?\)/g)) {
          if (!src.startsWith('data:')) this.seen.add(new URL(src, location.href).href)
        }
      }
      for (const entry of performance.getEntriesByType('resource')) {
        if (!Arrivals.picture.test(entry.name) || this.done.has(entry.name)) continue
        this.done.add(entry.name)
        this.seen.add(entry.name)
        this.lastDone = Math.max(this.lastDone, entry.responseEnd)
      }
      return this.seen.size ? this.done.size / this.seen.size : 0
    }

    /** Whether everything the page asked for is in, and nothing has come in for a moment, so nothing more is coming. */
    settled(now) {
      if (!this.loaded || now - this.loadedAt < 200 || now - this.lastDone < 300) return false
      for (const img of document.images) if (!img.complete) return false
      return true
    }
  }

  /** The overlay: the crows over the page while it loads. */
  class Loader {
    constructor() {
      this.still = matchMedia('(prefers-reduced-motion: reduce)').matches
      this.started = performance.now()
      this.arrivals = new Arrivals()
      this.loop = read(source.textContent)
      // With ?loader in the address the crows stay up, to be looked at.
      this.kept = new URLSearchParams(location.search).has('loader')
      // The loop is played through at least once a session; after that the paper only waits for the page.
      try {
        this.seen = sessionStorage.getItem('loader') === 'played'
      } catch {
        this.seen = false
      }

      const style = document.createElement('style')
      style.textContent = `
html:has(#loader>.ldr-paper){overflow:hidden}
#loader{position:fixed;inset:0;z-index:2147483647}
#loader .ldr-paper{position:absolute;inset:0;overflow:hidden;background:#47a2c4}
#loader pre{position:absolute;left:0;top:0;margin:0;font-family:${FONT};font-weight:400;line-height:1;white-space:pre;font-kerning:none;font-variant-ligatures:none;user-select:none;opacity:0;animation:ldr-in .3s ${QUICK}ms ease-out forwards}
@keyframes ldr-in{to{opacity:1}}`
      document.head.appendChild(style)
      this.style = style

      root.setAttribute('role', 'progressbar')
      root.setAttribute('aria-label', 'Loading')
      this.paper = document.createElement('div')
      this.paper.className = 'ldr-paper'
      this.paper.setAttribute('aria-hidden', 'true')
      root.appendChild(this.paper)
      this.type = new Type(this.paper, this.loop)
      this.type.show(this.loop.order[0])
      this.relay = () => {
        this.type.lay()
        this.type.show(this.loop.order[this.at || 0])
      }
      addEventListener('resize', this.relay)

      this.lastTake = -Infinity
      this.frame = requestAnimationFrame((now) => this.tick(now))
    }

    tick(now) {
      const age = now - this.started
      if (now - this.lastTake > 200) {
        this.lastTake = now
        const share = this.arrivals.take()
        const patience = 1 - Math.exp(-Math.max(0, age) / PATIENCE)
        root.setAttribute('aria-valuenow', String(Math.round(Math.min(1, Math.max(patience, share * 0.6)) * 100)))
        if (!this.kept && (this.arrivals.settled(now) || age > GIVE_UP)) {
          // In before the crows were shown, or shown already this session: the paper is just lifted.
          if (age < QUICK || this.seen || this.still) return this.leave(false)
          // Otherwise the crows get round their loop once before they go.
          const { fps, order } = this.loop
          if (age - QUICK >= (order.length * 1000) / fps) return this.leave(true)
        }
      }
      if (!this.still) {
        const { fps, order } = this.loop
        // A frame's time is when it began, which can be a moment before the loader did.
        this.at = Math.floor((Math.max(0, now - this.started) * fps) / 1000) % order.length
        this.type.show(order[this.at])
      }
      this.frame = requestAnimationFrame((next) => this.tick(next))
    }

    /** Takes the paper away: the type broken up first if `scattered`, or lifted plainly. */
    leave(scattered) {
      cancelAnimationFrame(this.frame)
      removeEventListener('resize', this.relay)
      const done = () => {
        cancelAnimationFrame(this.type.frame)
        root.replaceChildren()
        root.removeAttribute('role')
        root.removeAttribute('aria-label')
        root.removeAttribute('aria-valuenow')
        this.style.remove()
      }
      const lift = () => {
        this.paper.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 260, easing: 'ease-in', fill: 'forwards' })
        setTimeout(done, 280)
      }
      if (!scattered) return lift()
      try {
        sessionStorage.setItem('loader', 'played')
      } catch {}
      root.style.pointerEvents = 'none'
      this.type.scatter(lift)
    }
  }

  new Loader()
})()
