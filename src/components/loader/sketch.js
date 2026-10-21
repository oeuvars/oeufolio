// The loader, run inline at the top of the body so it is drawn before the bundle, the fonts or a single picture
// arrive. अनुराग is a dot-to-dot puzzle: a pencil joins the numbered dots in writing order as the page's pictures
// come in, the headline last, as the name is written by hand. Once everything is in, the dots burst into confetti
// over the page. It is a classic script, not a module: no imports, and nothing left on window.
;(() => {
  const root = document.getElementById('loader')
  if (!root) return

  const SVG = 'http://www.w3.org/2000/svg'
  const INK = '#1d1c1a'
  const PAPER = '#ebeae4'
  const CONFETTI = ['#b8263d', '#4b6cb0', '#6b3b5c', '#2f6a4e', '#e6c35a']
  const YELLOW = CONFETTI[4]
  // A page in by this is from the cache, and the paper is lifted straight off it without the puzzle being joined.
  const QUICK = 250
  // How long the line takes to get most of the way when nothing is known of what is still to come, in ms.
  const PATIENCE = 9000
  // Past this the page is shown as it is, so a request that never ends cannot hold it shut.
  const GIVE_UP = 120000

  // The centrelines of अ न ु र ा ग in the order they are written, the headline across them last, in units where the
  // headline is at 68 and the line the letters stand on at 160. Every point a segment ends on is a dot.
  const STROKES = [
    'M24 77C32 66 50 63 58 74C66 86 60 104 44 106C62 106 68 120 66 132C62 150 34 152 20 138',
    'M58 108C68 118 82 121 98 112',
    'M98 68C96.8 99 99.2 130 98 160',
    'M131 124C125 118 124 111 128 106C143 107.4 160 104.8 175 106',
    'M175 68C176.2 99 173.8 130 175 160',
    'M157 170C166 161 186 163 190 179C193 195 176 198 166 196C150 193 136 184 128 174',
    'M236 68C235.4 79 236.6 90 236 100C236 110 228 114 220 114C212 114 207 110 203 106',
    'M220 117C228 128 236 146 242 158',
    'M277 68C278 99 276 130 277 160',
    'M321 68C320.2 88 321.6 108 321 127C312 127 307 118 308 110',
    'M360 68C358.9 99 361.1 130 360 160',
    'M77 68C180 66.4 280 69.8 384 68',
  ]
  const VIEW = [6, 40, 398, 172]

  // Numerals written with a pen, five wide and nine tall.
  const DIGITS = [
    'M2.5 0C.6 0 0 2.4 0 4.5S.6 9 2.5 9 5 6.6 5 4.5 4.4 0 2.5 0Z',
    'M.8 1.8L2.8 0V9',
    'M.3 2C.6.4 4.6-.2 4.7 2.3 4.8 4.4 1.5 6.2.2 9H5',
    'M.4 1C2.2-.4 5 .3 4.6 2.3 4.3 3.8 2.6 4.2 1.8 4.3 4 4.3 5.2 5.6 4.8 7.2 4.3 9.3 1.4 9.4.2 8.2',
    'M3.8 9V0L0 6.4H5.2',
    'M4.8 0H1.1L.6 4C2.3 3 4.9 3.5 5 6 5.1 8.5 2.2 9.6.2 8.3',
    'M4.3.3C1.5.6 0 3.3.2 6.2.4 8.4 1.6 9.1 2.7 9 4.3 8.9 5 7.6 4.9 6.2 4.8 4.4 3.4 3.7 2.4 3.8 1.3 3.9.6 4.6.3 5.6',
    'M0 .2H5L1.8 9',
    'M2.6 4.3C.6 3.9.3 2.4.6 1.4 1 .2 4.1 0 4.5 1.5 4.9 3 3.6 3.9 2.6 4.3.7 4.9 0 6.1.3 7.5.7 9.2 4.4 9.4 4.9 7.4 5.2 5.9 4.1 4.8 2.6 4.3Z',
    'M4.7 3.4C4.4 4.9 2.2 5.4 1 4.7-.3 3.9 0 1.5 1.4.6 2.9-.3 4.8.6 4.8 2.6V9',
  ]

  // The pencil, its point at the origin and its length along x: lead, sharpened wood, a yellow hexagonal body, the
  // ferrule and the eraser.
  const PENCIL = [
    ['M14-3.6L1.6-.7Q0 0 1.6.7L14 3.6Z', PAPER],
    ['M5.2-1.5L1.6-.7Q0 0 1.6.7L5.2 1.5Q4.4 0 5.2-1.5Z', INK],
    ['M14-3.6H48V3.6H14Q12.8 0 14-3.6Z', YELLOW],
    ['M14.6-1.2H48M14.6 1.2H48', null],
    ['M48-3.6H53.5V3.6H48ZM49.8-3.6V3.6M51.6-3.6V3.6', PAPER],
    ['M53.5-3.3H57.4Q60.4-3.3 60.4 0T57.4 3.3H53.5Z', CONFETTI[0]],
  ]

  /** A seeded random, so the hand's wobble is the same on every visit. */
  const random = (seed) => () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }

  const element = (name, attributes, parent) => {
    const node = document.createElementNS(SVG, name)
    for (const key in attributes) node.setAttribute(key, attributes[key])
    if (parent) parent.appendChild(node)
    return node
  }

  /** A path of absolute M and C commands, read into its numbers and the points its segments end on. */
  const parse = (d) => {
    const tokens = d.match(/[MC]|-?\d*\.?\d+/g)
    const commands = []
    for (let i = 0; i < tokens.length; ) {
      const letter = tokens[i++]
      const values = []
      while (i < tokens.length && !/[MC]/.test(tokens[i])) values.push(+tokens[i++])
      for (let j = 0; j < values.length; j += letter === 'M' ? 2 : 6) commands.push([letter, values.slice(j, j + (letter === 'M' ? 2 : 6))])
    }
    return commands
  }
  const print = (commands) => commands.map(([letter, values]) => letter + values.map((v) => v.toFixed(2)).join(' ')).join('')

  /** The pictures the page has asked for and how many of them are in, by URL, so the puzzle can be joined that far. */
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

    /** Counts what is asked for in the markup so far and what has come in. */
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

  /** The puzzle on the paper: the dots and their numbers, the line joined so far, and the pencil joining it. */
  class Puzzle {
    constructor(svg, still) {
      this.still = still
      const rand = random(7)
      const measure = element('g', { visibility: 'hidden' }, svg)
      const rings = element('g', {}, svg)
      const lines = element('g', { fill: 'none', stroke: INK, 'stroke-width': 2.1, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, svg)
      const dots = element('g', { fill: INK }, svg)
      const numbers = element('g', { fill: 'none', stroke: INK, 'stroke-opacity': 0.72, 'stroke-width': 1.3, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, svg)

      // Each stroke as its true path to measure along, and as three tracings of it a hand never quite repeats,
      // swapped a few times a second as a drawing does when it is filmed frame by frame.
      this.strokes = STROKES.map((d) => {
        const commands = parse(d)
        const base = element('path', { d }, measure)
        const tracings = [0, 1, 2].map(() =>
          print(commands.map(([letter, values]) => [letter, values.map((v) => v + (rand() - 0.5) * 1.5)])),
        )
        const line = element('path', { d: tracings[0], pathLength: 1, 'stroke-dasharray': '1 2', 'stroke-dashoffset': 1, visibility: 'hidden' }, lines)
        // The dots are where each segment ends, at their lengths along the stroke.
        const ends = []
        for (let k = 0; k < commands.length; k++) {
          const values = commands[k][1]
          const x = values[values.length - 2]
          const y = values[values.length - 1]
          const along = k === 0 ? 0 : element('path', { d: print(commands.slice(0, k + 1)) }, measure).getTotalLength()
          ends.push({ x, y, along })
        }
        return { base, line, tracings, ends, length: base.getTotalLength() }
      })

      // The pencil's way: along each stroke, then lifted across to the start of the next.
      this.legs = []
      let total = 0
      this.strokes.forEach((stroke, i) => {
        this.legs.push({ stroke, from: total, span: stroke.length })
        total += stroke.length
        const next = this.strokes[i + 1]
        if (!next) return
        const a = stroke.ends[stroke.ends.length - 1]
        const b = next.ends[0]
        const span = Math.hypot(b.x - a.x, b.y - a.y) * 0.5
        this.legs.push({ from: total, span, a, b })
        total += span
      })
      this.total = total

      // Every dot, numbered in the order it is reached, a dot shared by two strokes counted once.
      const samples = []
      for (const stroke of this.strokes) for (let s = 0; s <= stroke.length; s += 3) samples.push(stroke.base.getPointAtLength(s))
      this.dots = []
      const taken = []
      for (const leg of this.legs) {
        if (!leg.stroke) continue
        for (const end of leg.stroke.ends) {
          if (this.dots.some((dot) => Math.hypot(dot.x - end.x, dot.y - end.y) < 1)) continue
          const ring = element('circle', { cx: end.x, cy: end.y, r: 4.8, fill: YELLOW, class: 'ldr-ring' }, rings)
          const dot = element('circle', { cx: end.x, cy: end.y, r: 2.3 }, dots)
          this.dots.push({ x: end.x, y: end.y, at: leg.from + end.along, ring, dot })
        }
      }
      // A number goes on whichever side of its dot is farthest from the line, the dots and the numbers already set.
      this.dots.forEach((dot, i) => {
        const label = String(i + 1)
        const width = label.length * 6.4 - 1.4
        let best = null
        for (let k = 0; k < 16; k++) {
          const angle = (k / 16) * Math.PI * 2
          const cx = dot.x + Math.cos(angle) * (6.5 + width * 0.25)
          const cy = dot.y + Math.sin(angle) * 7.5
          let room = Infinity
          for (const p of samples) room = Math.min(room, Math.hypot(p.x - cx, p.y - cy) - 2)
          for (const t of taken) room = Math.min(room, Math.hypot(t.x - cx, t.y - cy) - 5)
          for (const other of this.dots) room = Math.min(room, Math.hypot(other.x - cx, other.y - cy) - 3)
          if (!best || room > best.room) best = { room, cx, cy }
        }
        taken.push({ x: best.cx, y: best.cy })
        const scale = 0.6
        const g = element('g', { transform: `translate(${best.cx - (width * scale) / 2} ${best.cy - 4.5 * scale}) scale(${scale})` }, numbers)
        ;[...label].forEach((digit, j) => element('path', { d: DIGITS[+digit], transform: `translate(${j * 6.4} 0)` }, g))
      })

      const pencil = element('g', { class: 'ldr-pencil', stroke: INK, 'stroke-width': 1.1, 'stroke-linejoin': 'round' }, svg)
      this.pencil = element('g', {}, pencil)
      for (const [d, fill] of PENCIL) element('path', { d, fill: fill || 'none' }, this.pencil)
      this.tracing = 0
      this.place(0, 0)
    }

    /** Joins the puzzle up to `progress` of the way, with the pencil at the end of the line. */
    place(progress, time) {
      const reach = progress * this.total
      let tip = null
      let lift = 0
      for (const leg of this.legs) {
        const into = Math.min(Math.max(reach - leg.from, 0), leg.span)
        if (leg.stroke) {
          const drawn = into / leg.span
          leg.stroke.line.setAttribute('visibility', drawn > 0 ? 'visible' : 'hidden')
          leg.stroke.line.setAttribute('stroke-dashoffset', String(1 - drawn))
          if (!tip && reach <= leg.from + leg.span) tip = leg.stroke.base.getPointAtLength(into)
        } else if (!tip && reach < leg.from + leg.span) {
          const u = into / leg.span
          tip = { x: leg.a.x + (leg.b.x - leg.a.x) * u, y: leg.a.y + (leg.b.y - leg.a.y) * u }
          lift = Math.sin(Math.PI * u) * 12
        }
      }
      tip = tip || this.strokes[this.strokes.length - 1].base.getPointAtLength(Infinity)
      for (const dot of this.dots) dot.ring.classList.toggle('ldr-hit', reach >= dot.at - 0.5)
      // A hand at rest still moves a little; one drawing leans into the stroke.
      const sway = this.still ? 0 : Math.sin(time / 420) * 1.6
      const bob = this.still ? 0 : Math.sin(time / 260) * 0.8
      this.pencil.setAttribute('transform', `translate(${tip.x} ${tip.y - lift + bob}) rotate(${-52 + sway})`)
    }

    /** The next of the three tracings, a few times a second. */
    boil() {
      if (this.still) return
      this.tracing = (this.tracing + 1) % 3
      for (const stroke of this.strokes) stroke.line.setAttribute('d', stroke.tracings[this.tracing])
    }

    /** The dots' places on the screen, for the confetti to burst from. */
    points() {
      return this.dots.map((dot) => {
        const box = dot.dot.getBoundingClientRect()
        return { x: box.left + box.width / 2, y: box.top + box.height / 2 }
      })
    }
  }

  /** The overlay: paper over the page while it loads, the puzzle on it, and the burst it leaves by. */
  class Loader {
    constructor() {
      this.still = matchMedia('(prefers-reduced-motion: reduce)').matches
      this.started = performance.now()
      this.arrivals = new Arrivals()
      this.progress = 0
      this.target = 0
      this.finishing = false
      // The name is written out and burst once a session; after that the paper only waits for the page.
      try {
        this.seen = sessionStorage.getItem('loader') === 'written'
      } catch {
        this.seen = false
      }

      const style = document.createElement('style')
      style.textContent = `
html:has(#loader>.ldr-paper){overflow:hidden}
#loader{position:fixed;inset:0;z-index:2147483647;pointer-events:auto}
#loader .ldr-paper{position:absolute;inset:0;background:${PAPER}}
#loader svg{opacity:0;animation:ldr-in .3s ${QUICK}ms ease-out forwards}
#loader svg{position:absolute;left:50%;top:50%;width:min(92vw,640px);height:auto;transform:translate(-50%,-56%);overflow:visible}
#loader .ldr-ring{transform-box:fill-box;transform-origin:center;transform:scale(0);transition:transform .32s cubic-bezier(.3,1.6,.5,1)}
#loader .ldr-ring.ldr-hit{transform:scale(1)}
#loader .ldr-confetti{position:fixed;left:0;top:0;border-radius:50%;pointer-events:none;will-change:transform,opacity}
@keyframes ldr-in{to{opacity:1}}
@media (prefers-reduced-motion:reduce){#loader .ldr-ring{transition:none}}`
      document.head.appendChild(style)
      this.style = style

      root.setAttribute('role', 'progressbar')
      root.setAttribute('aria-label', 'Loading')
      root.setAttribute('aria-valuemin', '0')
      root.setAttribute('aria-valuemax', '100')
      this.paper = document.createElement('div')
      this.paper.className = 'ldr-paper'
      root.appendChild(this.paper)
      const svg = element('svg', { viewBox: VIEW.join(' '), 'aria-hidden': 'true' }, this.paper)
      this.puzzle = new Puzzle(svg, this.still)

      this.lastBoil = 0
      this.lastTake = -Infinity
      this.last = performance.now()
      this.frame = requestAnimationFrame((now) => this.tick(now))
    }

    tick(now) {
      // The page's own start-up can hold the frames back a good while; the pencil keeps to the clock, not the frames.
      const dt = Math.min(now - this.last, 500) / 1000
      this.last = now
      const age = now - this.started

      if (now - this.lastTake > 200) {
        this.lastTake = now
        const share = this.arrivals.take()
        // The small pictures come in first and the large ones last, so how many are in says little of how long is
        // left. The line runs on at a pace that slows as it goes, and the pictures that are in can only hurry it. It
        // stops short of the headline's end, the last of it for when all are in.
        const patience = 1 - Math.exp(-age / PATIENCE)
        this.target = Math.max(this.target, Math.min(1, Math.max(patience, share * 0.6)) * 0.94)
        root.setAttribute('aria-valuenow', String(Math.round(this.progress * 100)))
        if (!this.finishing && (this.arrivals.settled(now) || age > GIVE_UP)) {
          // In before the puzzle was shown, or the name was already written for this visitor in this session: the paper
          // is just lifted, with nothing to finish.
          if (age < QUICK || this.seen) return this.leave(false)
          this.finishing = true
          this.target = 1
        }
      }

      // The pencil goes toward what is in, never faster than a hand writes; once all is in, quick enough that the
      // name is done in a second and a half.
      const pace = this.finishing ? Math.max(0.7, (1 - this.progress) / 1.5) : 0.22
      if (this.progress < this.target) this.progress = Math.min(this.target, this.progress + Math.max(pace * dt * Math.min(1, (this.target - this.progress) * 6), 0.02 * dt))
      if (this.still && this.finishing) this.progress = 1

      if (now - this.lastBoil > 110) {
        this.lastBoil = now
        this.puzzle.boil()
      }
      this.puzzle.place(this.progress, now)

      if (this.finishing && this.progress >= 1) return this.leave(!this.still)
      this.frame = requestAnimationFrame((next) => this.tick(next))
    }

    /** Lifts the paper off the page. */
    fade(duration = 500) {
      this.paper.animate([{ opacity: 1 }, { opacity: 0 }], { duration, easing: 'ease-in', fill: 'forwards' })
    }

    /** Takes the paper away, the dots bursting over the page as it goes if `burst`. */
    leave(burst) {
      cancelAnimationFrame(this.frame)
      const done = () => {
        root.replaceChildren()
        root.removeAttribute('role')
        root.removeAttribute('aria-label')
        this.style.remove()
      }
      if (!burst) {
        this.fade(200)
        return setTimeout(done, 220)
      }
      // The pencil is lifted away and every dot throws a handful of confetti across the paper. The paper is lifted
      // as the confetti falls, so the last of it comes down over the page.
      this.puzzle.pencil.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 260, easing: 'ease-in', fill: 'forwards' })
      setTimeout(() => {
        const rand = random(31)
        const from = this.puzzle.points()
        const reach = Math.hypot(innerWidth, innerHeight) * 0.5
        for (let i = 0; i < 220; i++) {
          const start = from[i % from.length]
          const size = 6 + rand() ** 1.6 * 16
          const angle = rand() * Math.PI * 2
          const distance = reach * (0.15 + rand() * 0.9)
          const piece = document.createElement('i')
          piece.className = 'ldr-confetti'
          piece.style.cssText = `width:${size}px;height:${size}px;background:${CONFETTI[Math.floor(rand() * CONFETTI.length)]}`
          root.appendChild(piece)
          const x = start.x - size / 2
          const y = start.y - size / 2
          const bx = x + Math.cos(angle) * distance
          const by = y + Math.sin(angle) * distance * 0.75
          const drift = (rand() - 0.5) * 60
          const fall = 140 + rand() * 220
          piece.animate(
            [
              { transform: `translate(${x}px,${y}px) scale(.3)`, opacity: 1, easing: 'cubic-bezier(.1,.75,.3,1)' },
              { transform: `translate(${bx}px,${by}px) scale(1)`, opacity: 1, offset: 0.3, easing: 'cubic-bezier(.45,0,.75,.55)' },
              { transform: `translate(${bx + drift * 0.7}px,${by + fall * 0.6}px) scale(.95)`, opacity: 1, offset: 0.75 },
              { transform: `translate(${bx + drift}px,${by + fall}px) scale(.9)`, opacity: 0 },
            ],
            { duration: 1800 + rand() * 800, delay: rand() * 90, fill: 'both' },
          )
        }
        root.style.pointerEvents = 'none'
        try {
          sessionStorage.setItem('loader', 'written')
        } catch {}
        setTimeout(() => this.fade(650), 380)
        setTimeout(done, 2900)
      }, 260)
    }
  }

  new Loader()
})()
