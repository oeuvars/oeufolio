// The loader, run inline at the top of the body so it is up before the bundle, the fonts or a single picture arrive.
// The Tetons at dusk, set in type (public/loader/tetons.txt, from studio/tetons/ascii.py), with the nine birds of
// PRS's fretboard inlays (birds.txt) flying left to right over them in mother of pearl, the farther ones smaller,
// slower and dimmer. A hiss of noise lies over it all, and now and then the picture tears for a moment like a bad
// signal: bands of it slip sideways, tinted. Once everything is in, the type goes out cell by cell and the picture is
// lifted. It is drawn on a canvas, one character to a cell. A classic script, not a module: no imports, nothing left
// on window.
;(() => {
  const root = document.getElementById('loader')
  const source = document.getElementById('loader-birds')
  if (!root || !source) return

  const ART = '/loader/tetons.txt'
  const FONT = 'Menlo,"SF Mono",ui-monospace,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace'
  // Menlo's width to its height, which the grids were set at.
  const ADVANCE = 0.602
  // The finest grid whose type is at least this many pixels is used, or else the coarsest.
  const SMALLEST = 7
  // The photograph, set as type: its shape, how much of the screen's height it fills at least, and about how far
  // down it the peaks stand, so the birds keep to the sky above them.
  const PHOTO = { width: 735, height: 359, fill: 0.7, peaks: 0.26 }
  // The sky's type above the photograph, where the screen is taller than it: its mark, and now and then another.
  const SKY = ':'
  const SKY_ELSE = ".:'.-"
  const SKY_ODD = 0.07
  // The birds, farthest first: which bird, how many rows tall, where along the crossing they start, how high, as a
  // share of the sky over the peaks, and how fast, in screen widths a second.
  const FLIGHTS = [
    { bird: 6, rows: 5, from: 0.1, high: 0.55, speed: 0.018 },
    { bird: 1, rows: 5, from: 0.62, high: 0.22, speed: 0.021 },
    { bird: 0, rows: 5, from: 0.86, high: 0.68, speed: 0.016 },
    { bird: 2, rows: 8, from: 0.36, high: 0.48, speed: 0.03 },
    { bird: 5, rows: 8, from: 0.78, high: 0.1, speed: 0.034 },
    { bird: 3, rows: 8, from: 0.02, high: 0.3, speed: 0.028 },
    { bird: 7, rows: 12, from: 0.55, high: 0.42, speed: 0.05 },
    { bird: 8, rows: 12, from: 0.2, high: 0.06, speed: 0.056 },
    { bird: 4, rows: 17, from: 0.72, high: 0.16, speed: 0.075 },
  ]
  // Mother of pearl: white with a sheen of pink, green and blue that drifts across each bird.
  const PEARL = [
    [238, 242, 244],
    [246, 226, 238],
    [226, 244, 234],
    [224, 234, 250],
  ]
  // The noise: a few tiles of speckle, one at a time at a random offset, swapped this often, in ms, at this opacity.
  const TILE = 128
  const TILES = 4
  const NOISE = 0.12
  const HISS = 50
  // The tears: the calm between them and how long each lasts, in ms; how often its bands are cut again while it does;
  // how many bands at most, how far they slip, in pixels, and the tints they take.
  const CALM = [1400, 3800]
  const TEAR = [90, 260]
  const CUT = [40, 70]
  const BANDS = 5
  const SLIP = 44
  const TINTS = ['rgba(255,255,255,.1)', 'rgba(0,0,0,.25)', 'rgba(255,48,128,.14)', 'rgba(0,255,236,.14)']
  // On the way out each bird's characters break down through these, a step every so often; the mountains' simply go.
  const DECAY = '%+:. '
  const STEP = 45
  const SCATTER = 520
  // A page in by this is from the cache, and the paper is lifted straight off without the picture being shown.
  const QUICK = 250
  // The first time in a session the picture is shown at least this long, in ms.
  const LINGER = 3600
  // How long the bar takes to get most of the way when nothing is known of what is still to come, in ms.
  const PATIENCE = 9000
  // Past this the page is shown as it is, so a request that never ends cannot hold it shut.
  const GIVE_UP = 120000

  const random = (seed) => () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }

  /** The mountains: the night they are set on, the colour of each of their sixteen steps, and their grids. */
  const readArt = (text) => {
    const lines = text.split('\n')
    const [night, ...colours] = lines[0].split(' ')
    const grids = []
    for (let i = 1; /^\d+ \d+$/.test(lines[i] || ''); ) {
      const [cols, rows] = lines[i].split(' ').map(Number)
      const chars = lines.slice(i + 1, i + 1 + rows)
      const levels = lines.slice(i + 1 + rows, i + 1 + 2 * rows)
      grids.push({ cols, rows, chars, levels })
      i += 1 + 2 * rows
    }
    return { night, colours, grids }
  }

  /** The birds, each at the heights it was set at, by rows. */
  const readBirds = (text) => {
    const lines = text.replace(/^\n+/, '').split('\n')
    const birds = []
    for (let i = 0; /^\d+ \d+ \d+$/.test(lines[i] || ''); ) {
      const [bird, rows, cols] = lines[i].split(' ').map(Number)
      ;(birds[bird] ||= {})[rows] = { rows, cols, lines: lines.slice(i + 1, i + 1 + rows) }
      i += 1 + rows
    }
    return birds
  }

  /** The noise over the picture, and the moments it tears like a bad signal. */
  class Static {
    constructor(paper) {
      this.rand = random(19)
      const canvas = document.createElement('canvas')
      canvas.width = canvas.height = TILE
      const context = canvas.getContext('2d')
      this.tiles = []
      for (let t = 0; t < TILES; t++) {
        const image = context.createImageData(TILE, TILE)
        for (let i = 0; i < image.data.length; i += 4) {
          // Each speck light or dark, the further from grey the more it shows.
          const v = this.rand()
          image.data.fill(v > 0.5 ? 255 : 0, i, i + 3)
          image.data[i + 3] = Math.abs(v - 0.5) * 510
        }
        context.putImageData(image, 0, 0)
        this.tiles.push(`url(${canvas.toDataURL()})`)
      }
      this.noise = document.createElement('div')
      this.noise.className = 'ldr-noise'
      paper.appendChild(this.noise)
      this.bands = []
      this.peaks = [0, innerHeight]
      this.hissed = 0
      this.next = performance.now() + this.between(CALM)
      this.end = 0
      this.recut = 0
      this.hiss()
    }

    between([lo, hi]) {
      return lo + this.rand() * (hi - lo)
    }

    hiss() {
      this.noise.style.backgroundImage = this.tiles[Math.floor(this.rand() * TILES)]
      this.noise.style.backgroundPosition = `${Math.floor(this.rand() * TILE)}px ${Math.floor(this.rand() * TILE)}px`
    }

    /** Moves the noise on, and starts, recuts or ends a tear while `tearing`. */
    tick(now, tearing) {
      if (now - this.hissed >= HISS) {
        this.hissed = now
        this.hiss()
      }
      if (!tearing) {
        this.bands = []
        return
      }
      if (!this.end && now >= this.next) {
        this.end = now + this.between(TEAR)
        this.recut = now
      }
      if (!this.end) return
      if (now >= this.end) {
        this.end = 0
        this.next = now + this.between(CALM)
        this.bands = []
      } else if (now >= this.recut) {
        this.recut = now + this.between(CUT)
        this.cut()
      }
    }

    /** Cuts a fresh set of bands: mostly thin lines and a few deeper strips, each slipped sideways and tinted. Most
     * cross the peaks, where a slip shows. */
    cut() {
      const count = 1 + Math.floor(this.rand() * BANDS)
      const [high, low] = this.peaks
      this.bands = []
      for (let i = 0; i < count; i++) {
        const top = this.rand() < 0.65 ? high + this.rand() * (low - high) : this.rand() * innerHeight
        const height = this.rand() < 0.4 ? 1 + this.rand() * 3 : 6 + this.rand() ** 2 * 60
        const shift = Math.round((this.rand() - 0.5) * 2 * SLIP)
        this.bands.push({ top, height, shift, tint: TINTS[Math.floor(this.rand() * TINTS.length)] })
      }
    }
  }

  /** The picture: the mountains set in type on a canvas, and the birds flying over them. */
  class Picture {
    constructor(paper, art, birds) {
      this.art = art
      this.birds = birds
      this.canvas = document.createElement('canvas')
      paper.insertBefore(this.canvas, paper.firstChild)
      this.context = this.canvas.getContext('2d')
      this.base = document.createElement('canvas')
      this.born = performance.now()
      this.rand = random(23)
      this.lay()
    }

    /** Sets the mountains on the screen as it is now, on the finest grid that keeps the type large enough. */
    lay() {
      const w = innerWidth
      const h = innerHeight
      const dpr = Math.min(devicePixelRatio || 1, 2)
      const wide = Math.max(w, ((h * PHOTO.fill) / PHOTO.height) * PHOTO.width)
      const grids = this.art.grids.slice().sort((a, b) => b.cols - a.cols)
      const grid = grids.find((each) => wide / (each.cols * ADVANCE) >= SMALLEST) || grids[grids.length - 1]
      const size = wide / (grid.cols * ADVANCE)
      const cell = size * ADVANCE
      const cols = Math.ceil(w / cell)
      const rows = Math.ceil(h / size)
      const left = Math.round((cols - grid.cols) / 2)
      const top = rows - grid.rows
      Object.assign(this, { w, h, dpr, size, cell, cols, rows })
      this.peaks = [(top + grid.rows * 0.2) * size, (top + grid.rows * 0.55) * size]
      this.sky = (top + grid.rows * PHOTO.peaks) * size

      // Each cell's character and step; where the screen is taller than the photograph, its sky goes on above.
      const skyLevel = parseInt(grid.levels[0][0], 16)
      const rand = random(23)
      this.cells = []
      const byLevel = this.art.colours.map(() => [])
      for (let r = 0; r < rows; r++) {
        const line = []
        for (let c = 0; c < cols; c++) {
          const gr = r - top
          const gc = c - left
          let char = ' '
          let level = 0
          if (gr < 0) {
            char = rand() < SKY_ODD ? SKY_ELSE[Math.floor(rand() * SKY_ELSE.length)] : SKY
            level = skyLevel
          } else if (gr < grid.rows && gc >= 0 && gc < grid.cols) {
            char = grid.chars[gr][gc] || ' '
            level = parseInt(grid.levels[gr][gc], 16)
          }
          line.push(char)
          if (char !== ' ') byLevel[level].push(r, c, char)
        }
        this.cells.push(line)
      }

      for (const canvas of [this.canvas, this.base]) {
        canvas.width = Math.round(w * dpr)
        canvas.height = Math.round(h * dpr)
      }
      this.canvas.style.width = `${w}px`
      this.canvas.style.height = `${h}px`
      const base = this.base.getContext('2d')
      base.setTransform(dpr, 0, 0, dpr, 0, 0)
      base.fillStyle = this.art.night
      base.fillRect(0, 0, w, h)
      this.font = `${size}px ${FONT}`
      base.font = this.font
      const metrics = base.measureText('M')
      const ascent = metrics.fontBoundingBoxAscent ?? size * 0.928
      const descent = metrics.fontBoundingBoxDescent ?? size * 0.236
      // Where CSS would put the baseline at a line height of one, as the grids were set.
      this.baseline = (size - (ascent + descent)) / 2 + ascent
      byLevel.forEach((list, level) => {
        base.fillStyle = this.art.colours[level]
        for (let i = 0; i < list.length; i += 3) base.fillText(list[i + 2], list[i + 1] * cell, list[i] * size + this.baseline)
      })
      this.order = null

      // Each flight at the height it was set nearest the one it was given, scaled with the screen's width, so a
      // phone's narrow sky is not crowded.
      const scale = Math.min(1.3, Math.max(0.4, w / 1200))
      this.flights = FLIGHTS.map((flight) => {
        const sizes = this.birds[flight.bird]
        const want = flight.rows * scale
        const rows = Object.keys(sizes)
          .map(Number)
          .reduce((best, n) => (Math.abs(n - want) < Math.abs(best - want) ? n : best))
        return { ...flight, shape: sizes[rows], dim: 0.5 + 0.5 * Math.min(1, flight.rows / 17), phase: flight.from * 7 }
      })
      this.context.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    /** Where a bird is `t` seconds in, in cells: across the screen and round again, rising and falling a little. */
    place(flight, t) {
      const span = this.cols + flight.shape.cols
      const c = Math.round(((flight.from * span + (flight.speed * this.w * t) / this.cell) % span) - flight.shape.cols)
      const y = flight.high * Math.max(0, this.sky - flight.shape.rows * this.size) + Math.sin(t * 0.8 + flight.phase) * this.size * 1.5
      return [c, Math.round(y / this.size)]
    }

    /** Draws the picture at `now`: the mountains, any tear through them, and the birds over them. On the way out,
     * `gone` says how far each of a bird's characters has broken down. */
    draw(now, bands, gone) {
      const { context, base, w, h, dpr, cell, size } = this
      context.drawImage(base, 0, 0, w, h)
      for (const { top, height, shift, tint } of bands) {
        context.drawImage(base, 0, top * dpr, base.width, height * dpr, shift, top, w, height)
        context.fillStyle = tint
        context.fillRect(0, top, w, height)
      }
      const t = Math.max(0, now - this.born) / 1000
      context.font = this.font
      for (const flight of this.flights) {
        const [c0, r0] = this.place(flight, t)
        const { lines } = flight.shape
        for (let r = 0; r < lines.length; r++) {
          const line = lines[r]
          for (let c = 0; c < line.length; c++) {
            let char = line[c]
            if (char === ' ') continue
            const x = (c0 + c) * cell
            if (x < -cell || x > w) continue
            if (gone) {
              const step = gone(flight, r, c)
              if (step >= DECAY.length - 1) continue
              if (step >= 0) char = DECAY[step]
            }
            const y = (r0 + r) * size
            // The bird is cut out of what lies behind it, and laid in pearl that shimmers as it goes.
            context.fillStyle = this.art.night
            context.fillRect(x, y, cell, size)
            const wave = (c * 0.35 + r * 0.6 + t * 1.6 + flight.phase) % PEARL.length
            const a = PEARL[Math.floor(wave)]
            const b = PEARL[(Math.floor(wave) + 1) % PEARL.length]
            const f = wave % 1
            const k = flight.dim
            context.fillStyle = `rgb(${(a[0] + (b[0] - a[0]) * f) * k},${(a[1] + (b[1] - a[1]) * f) * k},${(a[2] + (b[2] - a[2]) * f) * k})`
            context.fillText(char, x, y + this.baseline)
          }
        }
      }
    }

    /** Puts the mountains' type out on the base, cell by cell in a random order, as far as `share` of it. */
    fade(share) {
      if (!this.order) {
        this.order = []
        for (let r = 0; r < this.rows; r++) for (let c = 0; c < this.cols; c++) if (this.cells[r][c] !== ' ') this.order.push(r * this.cols + c)
        for (let i = this.order.length - 1; i > 0; i--) {
          const j = Math.floor(this.rand() * (i + 1))
          ;[this.order[i], this.order[j]] = [this.order[j], this.order[i]]
        }
        this.faded = 0
      }
      const base = this.base.getContext('2d')
      base.fillStyle = this.art.night
      const until = Math.min(this.order.length, Math.round(share * this.order.length))
      for (; this.faded < until; this.faded++) {
        const i = this.order[this.faded]
        base.fillRect((i % this.cols) * this.cell, Math.floor(i / this.cols) * this.size, this.cell + 0.5, this.size + 0.5)
      }
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

  /** The overlay: the picture over the page while it loads. */
  class Loader {
    constructor() {
      this.still = matchMedia('(prefers-reduced-motion: reduce)').matches
      this.started = performance.now()
      this.arrivals = new Arrivals()
      this.birds = readBirds(source.textContent)
      // With ?loader in the address the picture stays up, to be looked at.
      this.kept = new URLSearchParams(location.search).has('loader')
      // The picture is shown for a while once a session; after that the paper only waits for the page.
      try {
        this.seen = sessionStorage.getItem('loader') === 'played'
      } catch {
        this.seen = false
      }

      const style = document.createElement('style')
      style.textContent = `
html:has(#loader>.ldr-paper){overflow:hidden}
#loader{position:fixed;inset:0;z-index:2147483647}
#loader .ldr-paper{position:absolute;inset:0;overflow:hidden;background:#04080e}
#loader canvas{position:absolute;left:0;top:0;opacity:0;animation:ldr-in .3s ease-out forwards}
#loader .ldr-noise{position:absolute;inset:0;background-size:${TILE}px;image-rendering:pixelated;opacity:0;animation:ldr-noise .3s ${QUICK}ms ease-out forwards}
@keyframes ldr-in{to{opacity:1}}
@keyframes ldr-noise{to{opacity:${NOISE}}}`
      document.head.appendChild(style)
      this.style = style

      root.setAttribute('role', 'progressbar')
      root.setAttribute('aria-label', 'Loading')
      this.paper = document.createElement('div')
      this.paper.className = 'ldr-paper'
      this.paper.setAttribute('aria-hidden', 'true')
      root.appendChild(this.paper)
      this.static = new Static(this.paper)
      this.relay = () => {
        if (!this.picture) return
        this.picture.lay()
        this.static.peaks = this.picture.peaks
        this.picture.draw(performance.now(), [])
      }
      addEventListener('resize', this.relay)

      // The mountains come as a file of their own, so the page's markup stays light; until they are in, the night
      // they are set on is shown.
      fetch(ART, { priority: 'high' })
        .then((reply) => (reply.ok ? reply.text() : Promise.reject(reply.status)))
        .then((text) => {
          if (this.left) return
          this.picture = new Picture(this.paper, readArt(text), this.birds)
          this.paper.style.background = this.picture.art.night
          this.static.peaks = this.picture.peaks
          this.shownAt = performance.now()
          this.picture.draw(this.shownAt, [])
        })
        .catch(() => {})

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
          // In before the picture was shown, shown already this session, or never come: the paper is just lifted.
          if (age < QUICK || this.seen || this.still || !this.picture) return this.leave(false)
          // Otherwise it stays a while before it goes.
          if (now - this.shownAt >= LINGER) return this.leave(true)
        }
      }
      if (!this.still && this.picture) {
        this.static.tick(now, true)
        this.picture.draw(now, this.static.bands)
      }
      this.frame = requestAnimationFrame((next) => this.tick(next))
    }

    /** Takes the paper away: the type put out first if `scattered`, or lifted plainly. */
    leave(scattered) {
      this.left = true
      cancelAnimationFrame(this.frame)
      removeEventListener('resize', this.relay)
      const done = () => {
        cancelAnimationFrame(this.frame)
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
      // Each bird's characters break down at a moment of their own, while the mountains' go out cell by cell and
      // the birds fly on.
      const rand = random(3)
      const moments = new Map()
      let age = 0
      const gone = (flight, r, c) => {
        const key = `${flight.bird}:${r}:${c}`
        if (!moments.has(key)) moments.set(key, rand() * SCATTER)
        return Math.floor((age - moments.get(key)) / STEP)
      }
      const start = performance.now()
      const frame = (now) => {
        age = Math.max(0, now - start)
        this.picture.fade(Math.min(1, age / SCATTER))
        this.static.tick(now, false)
        this.picture.draw(now, [], gone)
        if (age < SCATTER + STEP * DECAY.length) this.frame = requestAnimationFrame(frame)
        else lift()
      }
      this.frame = requestAnimationFrame(frame)
    }
  }

  new Loader()
})()
