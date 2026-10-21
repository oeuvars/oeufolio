// The loader, run inline at the top of the body so it is up before the bundle, the fonts or a single picture arrive.
// The Tetons at dusk, set in type, with a distant flock of the birds of PRS's fretboard inlays flying left to right
// over them in a loose V, in mother of pearl. The type is set here, on whatever grid fits the
// screen at about five pixels a character, from the photograph as studio/tetons/ascii.py worked it over
// (public/loader/tetons.webp: each point's colour, and the tone that picks its character) and the ridge it traced
// (public/loader/tetons.txt, with the birds). A hiss of noise lies over it all, and now and then the picture tears for
// a moment like a weak signal: a line or two of it slips sideways. Once everything is in, the type goes out cell by cell
// and the picture is lifted. It is drawn on a canvas, one character to a cell. A classic script, not a module: no
// imports, nothing left on window.
;(() => {
  const root = document.getElementById('loader')
  if (!root) return

  const ART = '/loader/tetons.txt'
  const SHEET = '/loader/tetons.webp'
  const FONT = 'Menlo,"SF Mono",ui-monospace,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace'
  // Menlo's width to its height, which the grids were set at.
  const ADVANCE = 0.602
  // The size of type, in pixels: a share of the screen's width, within bounds.
  const TYPE = { share: 1 / 280, least: 4.5, most: 7 }
  // A cell is a stroke of the ridge where between these shares of it are sky.
  const RIDGE = [0.15, 0.85]
  // How much noise is added to each cell's tone, so like tones do not band.
  const DITHER = 0.04
  // The photograph, set as type: its shape, how much of the screen's height it fills at least, and about how far
  // down it the peaks stand, so the birds keep to the sky above them.
  const PHOTO = { width: 735, height: 359, fill: 0.7, peaks: 0.26 }
  // The sky's type: its mark, and now and then another.
  const SKY = ':'
  const SKY_ELSE = ".:'.-"
  const SKY_ODD = 0.07
  // The flock: how many birds, the nine of the PRS set in turn; how tall each is, in pixels on a screen 1440 wide;
  // how far apart they fly, in birds' widths and heights; where along its crossing it starts; how high, as a share of
  // the sky over the peaks; and how fast, in screen widths a second.
  const FLOCK = { count: 17, height: 24, apart: [1.1, 0.5], from: 0.3, high: 0.42, speed: 0.024 }
  // How bright the pearl is at the flock's distance.
  const DISTANCE = 0.9
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
  const NOISE = 0.07
  const HISS = 50
  // The tears: the calm between them and how long each lasts, in ms; how often its bands are cut again while it does;
  // how many bands at most, how far they slip, in pixels, and the tints they take.
  const CALM = [5000, 11000]
  const TEAR = [60, 140]
  const CUT = [50, 80]
  const BANDS = 2
  const SLIP = 12
  const TINTS = ['rgba(255,255,255,.05)', 'rgba(0,0,0,.12)', 'rgba(255,48,128,.06)', 'rgba(0,255,236,.06)']
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

  /** What the loader was given: the night, the sky's colour, the ramp, the ridge, and the birds, each at the
   * heights it was set at, by rows. */
  const read = (text) => {
    const lines = text.split('\n')
    const [night, sky, ramp] = lines
    const ridge = lines[3].split(' ').map(Number)
    const birds = []
    for (let i = 4; /^\d+ \d+ \d+$/.test(lines[i] || ''); ) {
      const [bird, rows, cols] = lines[i].split(' ').map(Number)
      ;(birds[bird] ||= {})[rows] = { rows, cols, lines: lines.slice(i + 1, i + 1 + rows) }
      i += 1 + rows
    }
    return { night, sky, ramp, ridge, birds }
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
        const height = this.rand() < 0.7 ? 1 + this.rand() * 2 : 4 + this.rand() ** 2 * 14
        const shift = Math.round((this.rand() - 0.5) * 2 * SLIP)
        this.bands.push({ top, height, shift, tint: TINTS[Math.floor(this.rand() * TINTS.length)] })
      }
    }
  }

  /** The picture: the mountains set in type on a canvas, and the birds flying over them. */
  class Picture {
    constructor(paper, art, sheet) {
      this.art = art
      this.sheet = sheet
      this.canvas = document.createElement('canvas')
      paper.insertBefore(this.canvas, paper.firstChild)
      this.context = this.canvas.getContext('2d')
      this.base = document.createElement('canvas')
      this.born = performance.now()
      this.rand = random(23)
      this.lay()
    }

    /** The photograph's colour or tone, `half` 0 or 1, read over a grid of `cols` by `rows` cells, the photograph
     * lying at `left`, `top`, `wide` by `tall` in cells: the browser averages each cell's points as it scales. */
    read(half, cols, rows, left, top, wide, tall) {
      const canvas = document.createElement('canvas')
      canvas.width = cols
      canvas.height = rows
      const context = canvas.getContext('2d', { willReadFrequently: true })
      context.imageSmoothingQuality = 'high'
      context.drawImage(this.sheet, 0, half * PHOTO.height, PHOTO.width, PHOTO.height, left, top, wide, tall)
      return context.getImageData(0, 0, cols, rows).data
    }

    /** Sets the mountains on the screen as it is now. */
    lay() {
      const w = innerWidth
      const h = innerHeight
      const dpr = Math.min(devicePixelRatio || 1, 2)
      const size = Math.min(TYPE.most, Math.max(TYPE.least, w * TYPE.share))
      const cell = size * ADVANCE
      const cols = Math.ceil(w / cell)
      const rows = Math.ceil(h / size)
      Object.assign(this, { w, h, dpr, size, cell, cols, rows })
      // The photograph along the foot of the screen, as wide as it and at least so tall, in cells.
      const wide = Math.max(w, ((h * PHOTO.fill) / PHOTO.height) * PHOTO.width)
      const tall = (wide * PHOTO.height) / PHOTO.width
      const pw = wide / cell
      const ph = tall / size
      const left = (cols - pw) / 2
      const top = rows - ph
      this.peaks = [h - tall * 0.8, h - tall * 0.45]
      this.sky = h - tall * (1 - PHOTO.peaks)

      const paint = this.read(0, cols, rows, left, top, pw, ph)
      const tone = this.read(1, cols, rows, left, top, pw, ph)
      const { ramp, ridge, night, sky } = this.art
      const rand = random(23)
      const ridgeAt = (x) => ridge[Math.min(ridge.length - 1, Math.max(0, Math.round(x)))]
      // Each cell's character, and its colour as the photograph has it; the type is drawn in white, then the
      // colours laid into it.
      const chars = new Array(cols * rows)
      const colours = new ImageData(cols, rows)
      const skyRgb = [1, 3, 5].map((i) => parseInt(sky.slice(i, i + 2), 16))
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const i = r * cols + c
          // Where the cell lies in the photograph, in its points, and how much of it is sky.
          const x = ((c + 0.5 - left) / pw) * PHOTO.width
          const y0 = ((r - top) / ph) * PHOTO.height
          const y1 = ((r + 1 - top) / ph) * PHOTO.height
          const edge = ridgeAt(x)
          const share = Math.min(1, Math.max(0, (edge - y0) / (y1 - y0)))
          let char
          let rgb = [paint[i * 4], paint[i * 4 + 1], paint[i * 4 + 2]]
          if (share >= RIDGE[1]) {
            char = rand() < SKY_ODD ? SKY_ELSE[Math.floor(rand() * SKY_ELSE.length)] : SKY
            rgb = skyRgb
          } else if (share > RIDGE[0]) {
            // The ridge, in a stroke the way it runs here; in the photograph's points, y runs down.
            const run = (ridgeAt(x + 3) - ridgeAt(x - 3)) / 6
            char = Math.abs(run) > 2.5 ? '|' : run < -0.35 ? '/' : run > 0.35 ? '\\' : '_'
          } else {
            const t = Math.min(0.999, Math.max(0, tone[i * 4] / 255 + (rand() - 0.5) * 2 * DITHER))
            char = ramp[Math.floor(t * ramp.length)]
          }
          chars[i] = char
          colours.data.set([...rgb, 255], i * 4)
        }
      }
      this.chars = chars

      for (const canvas of [this.canvas, this.base]) {
        canvas.width = Math.round(w * dpr)
        canvas.height = Math.round(h * dpr)
      }
      this.canvas.style.width = `${w}px`
      this.canvas.style.height = `${h}px`
      const base = this.base.getContext('2d')
      base.setTransform(dpr, 0, 0, dpr, 0, 0)
      this.font = `${size}px ${FONT}`
      base.font = this.font
      const metrics = base.measureText('M')
      const ascent = metrics.fontBoundingBoxAscent ?? size * 0.928
      const descent = metrics.fontBoundingBoxDescent ?? size * 0.236
      // Where CSS would put the baseline at a line height of one, as the birds were set.
      this.baseline = (size - (ascent + descent)) / 2 + ascent
      base.fillStyle = '#fff'
      for (let i = 0; i < chars.length; i++) {
        if (chars[i] !== ' ') base.fillText(chars[i], (i % cols) * cell, Math.floor(i / cols) * size + this.baseline)
      }
      const tint = document.createElement('canvas')
      tint.width = cols
      tint.height = rows
      tint.getContext('2d').putImageData(colours, 0, 0)
      base.globalCompositeOperation = 'source-in'
      base.imageSmoothingEnabled = false
      base.drawImage(tint, 0, 0, cols * cell, rows * size)
      base.globalCompositeOperation = 'destination-over'
      base.fillStyle = night
      base.fillRect(0, 0, w, h)
      base.globalCompositeOperation = 'source-over'
      this.order = null

      // The flock: each bird at the height it was set nearest the flock's, a little larger or smaller as birds are,
      // in a loose V behind the leader, its arms trailing up and down and back, every place a little off true.
      const want = (FLOCK.height * Math.min(1.3, Math.max(0.55, w / 1440))) / size
      const nearest = (sizes, n) => sizes[Object.keys(sizes).map(Number).reduce((best, k) => (Math.abs(k - n) < Math.abs(best - n) ? k : best))]
      const flock = random(31)
      const shapes = Array.from({ length: FLOCK.count }, (_, i) => nearest(this.art.birds[i % this.art.birds.length], want * (0.9 + flock() * 0.2)))
      // A bird's room in the V, from the birds as they were set.
      const unit = [(shapes.reduce((sum, shape) => sum + shape.cols, 0) / shapes.length) * cell, (shapes.reduce((sum, shape) => sum + shape.rows, 0) / shapes.length) * size]
      this.flock = shapes.map((shape, i) => {
        const rank = Math.ceil(i / 2)
        const side = i % 2 ? -1 : 1
        return {
          id: i,
          shape,
          x: -rank * unit[0] * FLOCK.apart[0] * (0.85 + flock() * 0.3),
          y: side * rank * unit[1] * FLOCK.apart[1] * (0.8 + flock() * 0.4),
          phase: flock() * Math.PI * 2,
        }
      })
      const reach = Math.max(...this.flock.map((bird) => -bird.x)) + unit[0]
      this.flock.width = reach
      this.flock.top = Math.max(-Math.min(...this.flock.map((bird) => bird.y)) + size, FLOCK.high * this.sky)
      this.context.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    /** Where a bird of the flock is `t` seconds in, in cells: the flock across the screen and round again, each
     * bird drifting a little about its place in it. */
    place(bird, t) {
      const span = this.w + this.flock.width
      const lead = ((FLOCK.from * span + FLOCK.speed * this.w * t) % span) - this.size
      const x = lead + bird.x + Math.sin(t * 0.9 + bird.phase) * this.cell * 1.5
      const y = this.flock.top + bird.y + Math.sin(t * 1.3 + bird.phase * 1.7) * this.size * 0.9
      return [Math.round(x / this.cell), Math.round(y / this.size)]
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
      for (const bird of this.flock) {
        const [c0, r0] = this.place(bird, t)
        const { lines } = bird.shape
        for (let r = 0; r < lines.length; r++) {
          const line = lines[r]
          for (let c = 0; c < line.length; c++) {
            let char = line[c]
            if (char === ' ') continue
            const x = (c0 + c) * cell
            if (x < -cell || x > w) continue
            if (gone) {
              const step = gone(bird, r, c)
              if (step >= DECAY.length - 1) continue
              if (step >= 0) char = DECAY[step]
            }
            const y = (r0 + r) * size
            // The bird is cut out of what lies behind it, and laid in pearl that shimmers as it goes.
            context.fillStyle = this.art.night
            context.fillRect(x, y, cell, size)
            const wave = (c * 0.35 + r * 0.6 + t * 1.6 + bird.phase) % PEARL.length
            const a = PEARL[Math.floor(wave)]
            const b = PEARL[(Math.floor(wave) + 1) % PEARL.length]
            const f = wave % 1
            const k = DISTANCE
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
        for (let i = 0; i < this.chars.length; i++) if (this.chars[i] !== ' ') this.order.push(i)
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

      // The picture comes as files of its own, so the page's markup stays light; until they are in, the night it is
      // set on is shown.
      const sheet = new Image()
      sheet.fetchPriority = 'high'
      sheet.src = SHEET
      Promise.all([
        fetch(ART, { priority: 'high' }).then((reply) => (reply.ok ? reply.text() : Promise.reject(reply.status))),
        sheet.decode(),
      ])
        .then(([text]) => {
          if (this.left) return
          this.picture = new Picture(this.paper, read(text), sheet)
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
      const gone = (bird, r, c) => {
        const key = `${bird.id}:${r}:${c}`
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
