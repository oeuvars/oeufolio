// The loader, run inline at the top of the body so it is drawn before the bundle, the fonts or a single picture
// arrive. It is a page out of a colouring book, drawn in the manner of Jay Cover's Woset: Anurag at a pulley
// clothesline, hanging the site's pages out to dry as their pictures come in, the badge, the letter, the poster,
// the mat and the ticket, each coloured in as it is pegged, and a little more of Dilly, his cat, sat watching, with
// each. Once everything is in, he is coloured too, a gust comes, and the sheet blows off the page. A classic script, not a module: no imports, nothing left on window.
;(() => {
  const root = document.getElementById('loader')
  if (!root) return

  const SVG = 'http://www.w3.org/2000/svg'
  const INK = '#1e1d1b'
  const PAPER = '#ebe9e3'
  const RED = '#b0283f'
  const BLUE = '#4d6cb3'
  const PLUM = '#5e3b5b'
  const GREEN = '#2d6a4a'
  const YELLOW = '#e5c25a'
  const GINGER = '#d0782f'
  const PINK = '#e39b94'
  const BLUSH = '#f0cfc8'
  // A page in by this is from the cache, and the paper is lifted straight off without the scene being played.
  const QUICK = 250
  // How long the pegging takes to get most of the way when nothing is known of what is still to come, in ms.
  const PATIENCE = 9000
  // Past this the page is shown as it is, so a request that never ends cannot hold it shut.
  const GIVE_UP = 120000

  // Capitals and a few small letters written with one pen, about ten wide and sixteen tall, as Woset's captions are.
  const GLYPHS = {
    A: [10, 'M0 16L5 0L10 16M2 10H8'],
    a: [9, 'M8 10C7 6 1 6 1 11.5S7 17 8 12M8 8V16'],
    N: [10, 'M0 16V0L10 16V0'],
    U: [10, 'M0 0V11C0 17 10 17 10 11V0'],
    R: [10, 'M0 16V0H5C10 0 10 8 5 8H0M5 8L10 16'],
    G: [10, 'M10 3C8 0 0-1 0 8S10 17 10 10H5'],
    H: [10, 'M0 0V16M10 0V16M0 8H10'],
    S: [10, 'M10 2C7-1 0 0 1 4S10 7 10 12 2 17 0 14'],
    i: [3, 'M1.5 7V16M1.5 2.6V3'],
    P: [10, 'M0 16V0H5C10 0 10 8 5 8H0'],
    E: [9, 'M9 0H0V16H9M0 8H7'],
    O: [10, 'M5 0C-1 0-1 16 5 16S11 0 5 0Z'],
    o: [8, 'M4 7C0 7 0 16 4 16S8 7 4 7Z'],
    T: [10, 'M0 0H10M5 0V16'],
    D: [10, 'M0 0V16H3C11 16 11 0 3 0Z'],
    Y: [10, 'M0 0L5 8 10 0M5 8V16'],
  }
  const CAPTION = [
    ['aNURaG  HANGS', 70, 58],
    ['HiS  PaGES  OUT', 104, 96],
    ['To  DRY', 188, 134],
  ]

  // The pages he hangs, in the order the site stacks them, each drawn about its top middle where it is pegged: its
  // outline, the colours it is filled with, and the drawing over them.
  const PAGES = [
    {
      // The badge: the card in its holder, its photo and its lines.
      width: 60,
      height: 84,
      outline: 'M-30 4Q-30 0-26 0H26Q30 0 30 4V80Q30 84 26 84H-26Q-30 84-30 80Z',
      fills: [
        ['M-30 4Q-30 0-26 0H26Q30 0 30 4V80Q30 84 26 84H-26Q-30 84-30 80Z', YELLOW],
        ['M-14 24H14V48H-14Z', BLUE],
      ],
      ink: 'M-9 10H9Q12 10 12 13T9 16H-9Q-12 16-12 13T-9 10ZM-14 24H14V48H-14ZM-5 34A5 5 0 1 0 5 34A5 5 0 1 0-5 34M-9 48C-8 41 8 41 9 48M-6 32C-9 29-5 25-3 28-3 25 1 24 2 27 4 25 7 27 6 30M-20 58C-12 56-4 60 4 58S16 56 20 58M-20 66C-10 64 0 68 10 66M-20 74C-14 72-8 76 0 74',
    },
    {
      // The letter on handmade paper, its bottom edge deckled, written over in a loose hand and signed.
      width: 64,
      height: 86,
      outline: 'M-32 0H32V82C28 86 26 80 22 84S14 82 10 85 2 81-2 84-10 81-14 85-22 81-26 84-30 82-32 83Z',
      fills: [['M-32 0H32V82C28 86 26 80 22 84S14 82 10 85 2 81-2 84-10 81-14 85-22 81-26 84-30 82-32 83Z', BLUE]],
      ink: 'M-24 14c3-5 5 5 8 0s5 5 8 0 5 5 8 0 5 5 8 0 5 5 8 0M-24 26c3-5 5 5 8 0s5 5 8 0 5 5 8 0 5 5 8 0M-24 38c3-5 5 5 8 0s5 5 8 0 5 5 8 0 5 5 8 0 5 5 8 0M-24 50c3-5 5 5 8 0s5 5 8 0 5 5 8 0M2 68c4-8 8 4 4 6s6-10 10-2 4 2 8 0',
    },
    {
      // The poster: a block of flats at night under the moon, a few of its windows lit.
      width: 68,
      height: 94,
      outline: 'M-34 0H34V94H-34Z',
      fills: [
        ['M-34 0H34V94H-34Z', PLUM],
        ['M-26 16A6 6 0 1 0-14 16A6 6 0 1 0-26 16ZM-15 40h8v9h-8zM7 40h8v9h-8zM-4 54h8v9h-8zM-15 68h8v9h-8z', YELLOW],
      ],
      ink: 'M-26 16A6 6 0 1 0-14 16A6 6 0 1 0-26 16M-22 94V34L0 22 22 34V94M-15 40h8v9h-8zM-4 40h8v9h-8zM7 40h8v9h-8zM-15 54h8v9h-8zM-4 54h8v9h-8zM7 54h8v9h-8zM-15 68h8v9h-8zM-4 68h8v9h-8zM7 68h8v9h-8zM-4 94V84h8v10',
    },
    {
      // The cutting mat with its grid, a record and a watch lying on it.
      width: 76,
      height: 76,
      outline: 'M-38 0H38V76H-38Z',
      fills: [
        ['M-38 0H38V76H-38Z', GREEN],
        ['M-27 42A17 17 0 1 0 7 42A17 17 0 1 0-27 42Z', INK],
        ['M15 58A7 7 0 1 0 29 58A7 7 0 1 0 15 58Z', PAPER],
      ],
      ink: 'M-27 42A17 17 0 1 0 7 42A17 17 0 1 0-27 42M-15 42A5 5 0 1 0-5 42A5 5 0 1 0-15 42M15 58A7 7 0 1 0 29 58A7 7 0 1 0 15 58M19 51V40M25 51V40M19 65V76M25 65V76M22 58L24.5 55',
      fine: 'M-38 19H38M-38 38H38M-38 57H38M-19 0V76M0 0V76M19 0V76',
    },
    {
      // The ticket off a roll, notched at its sides, its stub on a perforation, a star stamped on it.
      width: 84,
      height: 44,
      outline: 'M-42 0H42V16A6 6 0 0 0 42 28V44H-42V28A6 6 0 0 0-42 16Z',
      fills: [
        ['M-42 0H42V16A6 6 0 0 0 42 28V44H-42V28A6 6 0 0 0-42 16Z', RED],
        ['M31 14L33.5 19.5 39 20 35 24 36.5 29.5 31 26.5 25.5 29.5 27 24 23 20 28.5 19.5Z', YELLOW],
      ],
      ink: 'M20 3V7M20 11V15M20 19V23M20 27V31M20 35V39M-32 12H8M-32 20C-24 18-16 22-8 20S4 18 8 20M-32 30H-4M-32 37H0M31 14L33.5 19.5 39 20 35 24 36.5 29.5 31 26.5 25.5 29.5 27 24 23 20 28.5 19.5Z',
    },
  ]

  // Where he pegs, and how far one pull of the line carries the pages along it.
  const PEG_AT = 340
  const SPACING = 84
  // The two runs of the pulley line, from the wheel on the post to the wheel on the tree.
  const UPPER = [104, 172, 400, 200, 696, 186]
  const LOWER = [104, 196, 400, 226, 696, 208]

  // Anurag, side on, facing the line: a mop of black curls, a big nose. His arms and legs are tubes, an ink stroke
  // with a narrower stroke of the cloth's colour down it; each of his poses is where his arms reach.
  const POSES = {
    rest: ['M178 324C168 352 168 378 172 400', 'M226 324C238 350 240 374 236 398'],
    up: ['M178 324C186 280 260 230 316 206', 'M226 324C262 290 318 236 364 206'],
    pull: ['M178 324C184 290 232 240 256 214', 'M226 324C252 292 282 248 296 216'],
    over: ['M178 324C184 290 216 240 240 212', 'M226 324C254 292 274 246 282 214'],
  }
  const BODY = {
    legs: ['M186 398C186 424 187 446 187 461', 'M220 398C226 424 230 446 233 461'],
    hips: 'M167 390H241L239 412H169Z',
    shoes: 'M172 471C171 461 187 458 194 462 202 464 206 470 202 472H174ZM222 471C221 461 237 458 244 462 252 464 256 470 252 472H224Z',
    torso: 'M165 394C161 368 161 342 168 322 174 308 190 302 204 302S234 306 240 322C246 342 246 368 243 394Z',
    collar: 'M195 303L204 316 213 303M220 336H234V347H220Z',
    head: 'M190 292C172 288 162 270 166 250 170 228 190 216 210 218 224 220 232 230 234 244 242 248 252 254 252 262S244 270 236 268C234 280 224 292 206 294Z',
    hair: 'M234 230C242 220 234 206 222 210 222 198 206 193 199 202 194 191 177 194 177 205 164 200 154 213 161 222 148 226 151 242 159 245 148 254 155 268 165 266 162 278 175 283 182 276L186 268C186 258 188 248 194 242 206 234 220 232 234 230Z',
    ear: 'M195 249C187 249 187 264 195 264',
    face: 'M215 239Q221 236 227 239M229 281Q233 283 237 280',
  }

  // What he stands in: the ground and its tufts and a flower, the post with its wheel, the tree with its wheel,
  // a cloud, the basket, and a bird on the post.
  const GROUND =
    'M24 474C140 469 260 477 400 472S640 476 784 470M98 474L93 459M104 474L105 454M110 474L117 461M430 473L426 461M436 473L438 457M560 472L556 460M566 472L571 462M752 471L748 458M758 471L762 455M608 472C609 456 606 446 610 436M610 436C602 432 602 424 609 424 608 416 617 416 616 424 624 422 625 431 617 432 620 440 611 441 610 436ZM610 452C618 446 624 448 626 452'
  const POST = 'M99 472V184M109 472V184M96 160H112M99 160V172M109 160V172M92 184A12 12 0 1 0 116 184A12 12 0 1 0 92 184M103 184h2'
  const TREE =
    'M692 472C695 400 688 320 692 196M712 472C709 400 716 320 712 196M684 197A12 12 0 1 0 708 197A12 12 0 1 0 684 197M695 197h2M712 300C724 292 732 284 736 272'
  const CLOUD = 'M520 92C506 92 504 74 520 74 520 60 540 56 548 66 556 54 578 58 578 72 594 70 598 92 580 92Z'
  const BASKET = 'M316 430H404V437H316ZM320 437H400L392 472H328ZM324 449H396M326 461H394M340 437L344 472M360 437V472M380 437L376 472'
  const BIRD = {
    outline: 'M92 150C92 140 102 134 112 138 118 140 120 146 118 150 114 154 96 156 92 150Z',
    body: 'M92 150C92 140 102 134 112 138 118 140 120 146 118 150 114 154 96 156 92 150ZM118 142L126 144 118 146M92 148L82 142 84 152ZM102 154V160M108 154V160',
    wing: ['M98 146C102 150 108 150 112 146', 'M100 146C98 132 110 130 112 146'],
  }

  // Dilly, his cat, a long-haired Turkish Van sat by the basket, facing out, drawn the way Schulz drew Snoopy: a big
  // round head on a small body, dot eyes with a glint, a button nose and a little mouth. Hers are the markings: a
  // ginger cap over her head and ears parted by a white blaze that runs to a point a little to her right, pale pink
  // ears, a ginger moustache either side of her nose, larger on her left, and a plume of a tail, solid ginger. Drawn
  // about the ground under her; her head turns about her neck.
  const DILLY = {
    at: [470, 472],
    size: 1.25,
    tail: 'M22-3C38-1 48-12 46-28C45-36 40-42 36-40 38-32 38-24 33-17 30-13 26-12 22-13Z',
    body: 'M-16-44C-24-36-26-16-24 0H24C26-16 24-36 16-44Z',
    legs: 'M-4-16V-1M4-16V-1M-14 0C-14-5-5-6-4 0M4 0C5-6 14-5 14 0',
    ears: 'M-24-68L-27-97Q-26.5-101-23-99L-5-82ZM24-68L27-97Q26.5-101 23-99L5-82Z',
    inner: 'M-21-73L-23-93-11-82ZM21-73L23-93 11-82Z',
    head: 'M-27-60C-28-74-18-84 0-84S28-74 27-60C26-48 14-41 0-41S-26-48-27-60Z',
    cap: [
      'M-2-84C-14-84-27-77-27-63-21-68-13-69-5-68Z',
      'M-2-84C14-84.5 27-77 27-63 21-68 13-69 5-68Z',
    ],
    patches: 'M-.5-53.5C2-55.5 6.5-55 7-52.5 6.5-50 2.5-49.5-.5-51ZM-3.5-53.5C-6-55.5-9.5-55-10-52.5-9.5-50-6-50-4-51.5Z',
    cheeks: [[-18, -52], [18, -52]],
    mouth: 'M0-52.5V-51M-4-49.5Q-2-47.5 0-51Q2-47.5 4-49.5',
    whiskers: 'M-15-54L-27-56M-15-51L-27-50M15-54L27-56M15-51L27-50',
    nose: 'M-3-55.5H3Q3-54 0-52.5-3-54-3-55.5Z',
    eyes: [-11, 11],
  }
  // Where she looks: how far her eyes shift and the tilt of her head, in degrees.
  const GAZES = { ahead: [0, 0, 4], him: [-2, -0.4, -6], line: [-1.4, -1.6, -10], bird: [-1.8, -1.8, -14] }

  /** A seeded random, so the hand's wobble is the same on every visit. */
  const random = (seed) => () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  const ease = (u) => (u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2)

  const element = (name, attributes, parent) => {
    const node = document.createElementNS(SVG, name)
    for (const key in attributes) node.setAttribute(key, attributes[key])
    if (parent) parent.appendChild(node)
    return node
  }
  const ink = (d, parent, width = 3) =>
    element('path', { d, fill: 'none', stroke: INK, 'stroke-width': width, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, parent)

  /** How high a run of the line is at `x`. */
  const along = ([x0, y0, cx, cy, x1, y1], x) => {
    let lo = 0
    let hi = 1
    for (let i = 0; i < 20; i++) {
      const t = (lo + hi) / 2
      if ((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1 < x) lo = t
      else hi = t
    }
    return (1 - lo) ** 2 * y0 + 2 * (1 - lo) * lo * cy + lo * lo * y1
  }

  let masks = 0
  /**
   * A colour laid in under the drawing, a little off its lines as a printed colour is, and wiped in with a crayon's
   * zigzag when it is coloured.
   */
  class Fill {
    constructor(defs, parent, d, colour, [x, y, w, h]) {
      const id = `ldr-mask-${masks++}`
      const mask = element('mask', { id, maskUnits: 'userSpaceOnUse', x: x - 20, y: y - 20, width: w + 40, height: h + 40 }, defs)
      // The crayon goes back and forth down the shape, each stroke wide enough to cover the gap to the next.
      const rows = Math.max(3, Math.round(h / 12))
      let zigzag = `M${x - 6} ${y - 4}`
      for (let i = 0; i <= rows; i++) zigzag += `L${i % 2 ? x - 6 : x + w + 6} ${(y - 4 + ((h + 8) * (i + 0.5)) / (rows + 1)).toFixed(1)}`
      this.stroke = element(
        'path',
        { d: zigzag, fill: 'none', stroke: '#fff', 'stroke-width': ((h / rows) * 1.7 + 6).toFixed(1), 'stroke-linecap': 'round', 'stroke-linejoin': 'round', pathLength: 1, 'stroke-dasharray': '1 2', 'stroke-dashoffset': 1 },
        mask,
      )
      element('path', { d, fill: colour, transform: 'translate(2.5 2.5)', mask: `url(#${id})` }, parent)
    }

    colour(duration) {
      if (!duration) return this.stroke.setAttribute('stroke-dashoffset', '0')
      this.stroke.animate([{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], { duration, easing: 'cubic-bezier(.4,.1,.6,1)', fill: 'forwards' })
    }
  }

  /** One of the site's pages, hung by two pegs, swinging on the line. */
  class Page {
    constructor(defs, parent, spec, index) {
      this.seed = index * 1.7
      this.angle = 0
      this.spin = 0
      this.lift = 0
      this.group = element('g', { visibility: 'hidden' }, parent)
      const body = element('g', { filter: 'url(#ldr-boil)' }, this.group)
      const box = [-spec.width / 2, 0, spec.width, spec.height]
      element('path', { d: spec.outline, fill: PAPER }, body)
      this.fills = spec.fills.map(([d, colour]) => new Fill(defs, body, d, colour, box))
      if (spec.fine) element('path', { d: spec.fine, fill: 'none', stroke: INK, 'stroke-width': 1.1, 'stroke-opacity': 0.55 }, body)
      ink(spec.ink, body, 2.2)
      ink(spec.outline, body, 2.8)
      // The pegs, sprung shut over the line.
      this.pegs = [-1, 1].map((side) => {
        const peg = element('g', { transform: `translate(${side * (spec.width / 2 - 9)} 0)` }, body)
        const inner = element('g', { class: 'ldr-peg' }, peg)
        element('path', { d: 'M-3.5-9H3.5V9H-3.5Z', fill: PAPER }, inner)
        ink('M-3.5-9H3.5V9H-3.5ZM-3.5 0H3.5', inner, 2)
        return inner
      })
    }

    /** Puts the page at `x` on the line, or `lift` below it in his hands, swinging as the breeze lets it. */
    place(x, time, wind, dt) {
      // A sheet on a line swings as a pendulum about its pegs: drawn back to hang straight, slowed by the air,
      // pushed about by the breeze.
      // A frame held back by the page's start-up is taken in short steps, so a long one cannot fling the sheet.
      const breeze = Math.sin(time / 900 + this.seed) * 0.6 + Math.sin(time / 370 + this.seed * 3) * 0.3
      for (let left = dt; left > 0; left -= 1 / 120) {
        const step = Math.min(left, 1 / 120)
        this.spin += (-this.angle * 22 - this.spin * 2.6 + (breeze + wind) * 14) * step
        this.angle += this.spin * step
      }
      const y = along(UPPER, x) + this.lift
      this.group.setAttribute('transform', `translate(${x.toFixed(2)} ${y.toFixed(2)}) rotate(${(this.lift ? 0 : this.angle).toFixed(2)})`)
    }
  }

  /** Anurag: his tubes of arms and legs, the poses he takes, his breathing and a blink now and then. */
  class Hanger {
    constructor(defs, parent) {
      const group = element('g', { filter: 'url(#ldr-boil)' }, parent)
      this.group = group
      const tube = (d, width = 13) => [
        element('path', { d, fill: 'none', stroke: INK, 'stroke-width': width, 'stroke-linecap': 'round' }, group),
        element('path', { d, fill: 'none', stroke: PAPER, 'stroke-width': width - 5.6, 'stroke-linecap': 'round' }, group),
      ]
      const hand = () => element('circle', { r: 7, fill: PAPER, stroke: INK, 'stroke-width': 3 }, group)
      this.back = tube(POSES.rest[0])
      this.backHand = hand()
      this.legs = BODY.legs.map((d) => tube(d, 19))
      element('path', { d: BODY.shoes, fill: INK }, group)
      element('path', { d: BODY.hips, fill: PAPER }, group)
      this.trousers = new Fill(defs, group, BODY.hips, BLUE, [163, 386, 82, 30])
      ink(BODY.hips, group)
      element('path', { d: BODY.torso, fill: PAPER }, group)
      this.shirt = new Fill(defs, group, BODY.torso, RED, [158, 298, 90, 98])
      ink(BODY.torso, group)
      ink(BODY.collar, group, 2.4)
      element('path', { d: BODY.head, fill: PAPER }, group)
      ink(BODY.head, group)
      element('path', { d: BODY.hair, fill: INK, stroke: INK, 'stroke-width': 3, 'stroke-linejoin': 'round' }, group)
      element('path', { d: BODY.ear, fill: PAPER }, group)
      ink(BODY.ear, group, 2.6)
      ink(BODY.face, group, 2.4)
      this.eye = element('circle', { cx: 222, cy: 249, r: 2.7, fill: INK }, group)
      this.lid = ink('M218.5 249.5H225.5', group, 2.2)
      this.lid.setAttribute('visibility', 'hidden')
      this.front = tube(POSES.rest[1])
      this.frontHand = hand()
      this.pose('rest')
      this.nextBlink = 1800
    }

    pose(name) {
      if (this.current === name) return
      this.current = name
      const [back, front] = POSES[name]
      for (const path of this.back) path.setAttribute('d', back)
      for (const path of this.front) path.setAttribute('d', front)
      const end = (d) => d.match(/(-?[\d.]+) (-?[\d.]+)$/).slice(1)
      ;[[this.backHand, end(back)], [this.frontHand, end(front)]].forEach(([hand, [x, y]]) => {
        hand.setAttribute('cx', x)
        hand.setAttribute('cy', y)
      })
    }

    /** Dresses him: his shirt and sleeves red, his trousers blue. */
    colour(duration) {
      this.shirt.colour(duration)
      this.trousers.colour(duration)
      const dye = ([, cloth], colour) => cloth.animate([{ stroke: PAPER }, { stroke: colour }], { duration: duration || 1, fill: 'forwards' })
      dye(this.back, RED)
      dye(this.front, RED)
      for (const leg of this.legs) dye(leg, BLUE)
    }

    tick(time, still) {
      if (still) return
      this.group.setAttribute('transform', `translate(0 ${(Math.sin(time / 700) * 0.8).toFixed(2)})`)
      if (time > this.nextBlink) {
        const shut = time < this.nextBlink + 130
        this.eye.setAttribute('visibility', shut ? 'hidden' : 'visible')
        this.lid.setAttribute('visibility', shut ? 'visible' : 'hidden')
        if (!shut) this.nextBlink = time + 2200 + ((time * 7) % 2400)
      }
    }
  }

  /**
   * Dilly. Like a cat on film she is still most of the time: her head goes pose to pose to whatever is moving and
   * holds there, her eyes ahead of it, her tail sweeps when a page goes up, and now and then she gives a slow blink.
   */
  class Dilly {
    constructor(defs, parent) {
      const group = element('g', { filter: 'url(#ldr-boil)', transform: `translate(${DILLY.at.join(' ')}) scale(${DILLY.size})` }, parent)
      // What is coloured of her as each page is pegged: her cap and ears first, so she is herself early, then her
      // tail, her moustache, her nose and the insides of her ears, and last her cheeks.
      const dye = (node, colour) => ({ colour: (duration) => node.animate([{ fill: PAPER }, { fill: colour }], { duration: duration || 1, fill: 'forwards' }) })
      this.tail = element('g', {}, group)
      element('path', { d: DILLY.tail, fill: PAPER }, this.tail)
      const tail = new Fill(defs, this.tail, DILLY.tail, GINGER, [20, -44, 30, 44])
      ink(DILLY.tail, this.tail)
      element('path', { d: DILLY.body, fill: PAPER }, group)
      ink(DILLY.body, group)
      ink(DILLY.legs, group, 2.4)
      this.head = element('g', {}, group)
      element('path', { d: DILLY.ears, fill: PAPER }, this.head)
      const ears = new Fill(defs, this.head, DILLY.ears, GINGER, [-28, -102, 56, 34])
      const inner = element('path', { d: DILLY.inner, fill: PAPER }, this.head)
      ink(DILLY.ears, this.head)
      element('path', { d: DILLY.head, fill: PAPER }, this.head)
      const cap = DILLY.cap.map((d) => new Fill(defs, this.head, d, GINGER, [-28, -86, 56, 22]))
      const cheeks = DILLY.cheeks.map(([cx, cy]) => dye(element('ellipse', { cx, cy, rx: 4, ry: 2.4, fill: PAPER }, this.head), BLUSH))
      const patches = new Fill(defs, this.head, DILLY.patches, GINGER, [-11, -56, 19, 7])
      ink(DILLY.head, this.head)
      ink(DILLY.mouth, this.head, 2)
      ink(DILLY.whiskers, this.head, 1.3)
      const nose = element('path', { d: DILLY.nose, fill: PAPER }, this.head)
      ink(DILLY.nose, this.head, 1.8)
      this.eyes = element('g', {}, this.head)
      this.pupils = []
      for (const x of DILLY.eyes) {
        const eye = element('g', {}, element('g', { transform: `translate(${x} -62)` }, this.eyes))
        element('ellipse', { rx: 2.6, ry: 3.6, fill: INK }, eye)
        element('circle', { cx: 0.9, cy: -1.4, r: 0.9, fill: PAPER }, eye)
        this.pupils.push(eye)
      }
      // Shut, her eyes are happy little arches.
      this.lids = ink(DILLY.eyes.map((x) => `M${x - 3.5} -61Q${x} -66 ${x + 3.5} -61`).join(''), this.head, 2.2)
      this.lids.setAttribute('visibility', 'hidden')
      this.parts = [[...cap, ears], [tail], [patches], [dye(nose, PINK), dye(inner, BLUSH)], cheeks]

      this.rand = random(23)
      this.gaze = 'ahead'
      this.hold = 2
      this.look = [0, 0]
      this.tilt = 0
      this.turn = 0
      this.sweep = 0
      this.swing = 0
      this.swishing = 0
      this.nextBlink = 3000
    }

    /** Turns her to `gaze`, held there for `hold` seconds before her attention wanders. */
    watch(gaze, hold = 2) {
      this.gaze = gaze
      this.hold = hold
    }

    /** One sweep of her tail. */
    swish() {
      this.swishing = 0.6
    }

    /** Colours in the `part`th of her. */
    colour(part, duration) {
      for (const piece of this.parts[part] || []) piece.colour(duration)
    }

    tick(time, dt, still) {
      if (still) return
      this.hold -= dt
      if (this.hold <= 0) this.watch(this.gaze === 'him' ? 'ahead' : 'him', 1.5 + this.rand() * 3)
      const [x, y, tilt] = GAZES[this.gaze]
      // Her eyes dart; her head and her tail are sprung, so they start slowly, arrive in about half a second and
      // settle by about one and a half.
      const dart = 1 - Math.exp(-dt * 18)
      this.look[0] += (x - this.look[0]) * dart
      this.look[1] += (y - this.look[1]) * dart
      this.swishing -= dt
      const sweep = this.swishing > 0 ? 20 : 0
      for (let left = dt; left > 0; left -= 1 / 120) {
        const step = Math.min(left, 1 / 120)
        this.turn += (-(this.tilt - tilt) * 36 - this.turn * 12) * step
        this.tilt += this.turn * step
        this.swing += (-(this.sweep - sweep) * 30 - this.swing * 7) * step
        this.sweep += this.swing * step
      }
      this.head.setAttribute('transform', `rotate(${this.tilt.toFixed(2)} 0 -44)`)
      this.tail.setAttribute('transform', `rotate(${this.sweep.toFixed(2)} 24 -8)`)
      for (const eye of this.pupils) eye.setAttribute('transform', `translate(${this.look[0].toFixed(2)} ${this.look[1].toFixed(2)})`)
      if (time > this.nextBlink) {
        const shut = time < this.nextBlink + 420
        this.eyes.setAttribute('visibility', shut ? 'hidden' : 'visible')
        this.lids.setAttribute('visibility', shut ? 'visible' : 'hidden')
        if (!shut) this.nextBlink = time + 4000 + this.rand() * 5000
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

  /** The colouring-book page: the scenery, the caption, Anurag, Dilly, his basket and the pages, and what they do next. */
  class Scene {
    constructor(svg, still) {
      this.still = still
      const defs = element('defs', {}, svg)
      // Lines drawn by hand never sit still on film: each frame is traced again, a little off the last.
      const boil = element('filter', { id: 'ldr-boil', x: '-10%', y: '-10%', width: '120%', height: '120%' }, defs)
      this.noise = element('feTurbulence', { type: 'fractalNoise', baseFrequency: 0.03, numOctaves: 1, seed: 1 }, boil)
      element('feDisplacementMap', { in: 'SourceGraphic', scale: still ? 0 : 2.6 }, boil)

      const rand = random(11)
      const scenery = element('g', { filter: 'url(#ldr-boil)' }, svg)
      ink(GROUND, scenery)
      ink(POST, scenery)
      // The tree's crown, a cloud of bumps, with its fruit.
      let crown = ''
      const bumps = 12
      for (let i = 0; i <= bumps; i++) {
        const a = (i / bumps) * Math.PI * 2 + 0.3
        const x = (704 + Math.cos(a) * 80).toFixed(1)
        const y = (116 + Math.sin(a) * 68).toFixed(1)
        const m = a - Math.PI / bumps
        const bulge = 1.22 + rand() * 0.1
        crown += i ? `Q${(704 + Math.cos(m) * 80 * bulge).toFixed(1)} ${(116 + Math.sin(m) * 68 * bulge).toFixed(1)} ${x} ${y}` : `M${x} ${y}`
      }
      element('path', { d: crown, fill: PAPER }, scenery)
      ink(crown, scenery)
      for (let i = 0; i < 9; i++) {
        const a = rand() * Math.PI * 2
        const r = Math.sqrt(rand()) * 52
        const cx = (704 + Math.cos(a) * r * 1.1).toFixed(1)
        const cy = (112 + Math.sin(a) * r * 0.85).toFixed(1)
        ink(`M${cx - 5} ${cy}A5 5 0 1 0 ${+cx + 5} ${cy}A5 5 0 1 0 ${cx - 5} ${cy}M${+cx + 1} ${cy - 5}l2-4`, scenery, 2.4)
      }
      ink(TREE, scenery)
      ink(CLOUD, scenery)
      ink(`M${UPPER[0]} ${UPPER[1]}Q${UPPER.slice(2).join(' ')}M${LOWER[0]} ${LOWER[1]}Q${LOWER.slice(2).join(' ')}`, scenery, 1.8)
      this.caption(scenery)

      // The basket, with the pages still to hang lying in it.
      const basket = element('g', { filter: 'url(#ldr-boil)' }, svg)
      this.sheets = PAGES.map((_, i) => {
        const sheet = element('g', { transform: `translate(${336 + i * 12} 433) rotate(${((rand() - 0.5) * 24).toFixed(1)})` }, basket)
        element('path', { d: 'M-11 2V-20H11V2Z', fill: PAPER }, sheet)
        ink('M-11 2V-20H11V2', sheet, 2.4)
        return sheet
      })
      element('path', { d: 'M316 430H404V437H316ZM320 437H400L392 472H328Z', fill: PAPER }, basket)
      ink(BASKET, basket)

      this.dilly = new Dilly(defs, svg)
      this.hanger = new Hanger(defs, svg)
      const line = element('g', {}, svg)
      this.pages = PAGES.map((spec, i) => new Page(defs, line, spec, i))
      this.bird = this.perch(svg)

      this.hung = 0
      this.queued = 0
      this.offset = 0
      this.wind = 0
      this.actions = []
      this.lastBoil = 0
    }

    /** Writes the caption out letter by letter, each a little off its neighbours' size and line. */
    caption(parent) {
      const rand = random(5)
      for (const [text, left, top] of CAPTION) {
        let x = left
        for (const letter of text) {
          if (letter === ' ') {
            x += 5
            continue
          }
          const [width, d] = GLYPHS[letter]
          const size = 1.25 + (rand() - 0.5) * 0.3
          const y = top + (rand() - 0.5) * 3 - 16 * size
          const g = element('g', { transform: `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${((rand() - 0.5) * 7).toFixed(1)} 5 8) scale(${size.toFixed(3)})` }, parent)
          ink(d, g, 2.6 / size)
          x += (width + 4.5) * size
        }
      }
    }

    /** The bird on the post, who flies off when the wind gets up. */
    perch(parent) {
      const group = element('g', { filter: 'url(#ldr-boil)' }, parent)
      element('path', { d: BIRD.outline, fill: PAPER }, group)
      ink(BIRD.body, group, 2.4)
      element('circle', { cx: 113, cy: 142, r: 1.8, fill: INK }, group)
      return { group, wing: ink(BIRD.wing[0], group, 2.4) }
    }

    /** Queues the next page: pull the line along, lift the page up to it, peg it and colour it. */
    hangNext(fast) {
      const index = this.queued++
      const page = this.pages[index]
      const k = fast ? 0.55 : 1
      if (index > 0) {
        let from = 0
        this.actions.push({
          duration: 760 * k,
          start: () => {
            from = this.offset
            this.dilly.watch('him', 1.6)
          },
          update: (u, time) => {
            this.offset = from + SPACING * ease(u)
            // Hand over hand.
            this.hanger.pose(u < 1 && Math.floor(time / 170) % 2 ? 'pull' : 'over')
          },
        })
      }
      this.actions.push({
        duration: 520 * k,
        start: () => {
          this.hung = index + 1
          this.sheets[PAGES.length - 1 - index].setAttribute('visibility', 'hidden')
          this.hanger.pose('up')
          this.dilly.watch('line', 2.4)
          page.group.setAttribute('visibility', 'visible')
        },
        update: (u) => (page.lift = (1 - ease(u)) * 70),
      })
      this.actions.push({
        duration: 260 * k,
        start: () => {
          page.lift = 0
          page.spin = 26
          this.dilly.swish()
          if (!this.still) for (const peg of page.pegs) peg.animate([{ transform: 'scale(0)' }, { transform: 'scale(1.25)' }, { transform: 'scale(1)' }], { duration: 260, easing: 'ease-out' })
        },
      })
      this.actions.push({
        duration: 700 * k,
        start: () => {
          this.hanger.pose('rest')
          page.fills.forEach((fill, i) => (this.still ? fill.colour(0) : setTimeout(() => fill.colour(520 * k), i * 160 * k)))
          if (this.still) this.dilly.colour(index, 0)
          else setTimeout(() => this.dilly.colour(index, 480 * k), page.fills.length * 160 * k + 120)
        },
      })
    }

    /** Queues the end: he is coloured in, the wind gets up and the bird leaves. */
    finish() {
      this.actions.push({
        duration: 700,
        start: () => {
          this.hanger.colour(this.still ? 0 : 600)
          this.dilly.watch('ahead', 1)
        },
      })
      this.actions.push({
        duration: 700,
        start: () => {
          if (this.still) return
          this.dilly.watch('bird', 4)
          this.dilly.swish()
          this.bird.wing.setAttribute('d', BIRD.wing[1])
          this.bird.group.animate(
            [{ transform: 'translate(0,0)' }, { transform: 'translate(-60px,-40px) rotate(-8deg)', offset: 0.4 }, { transform: 'translate(-220px,-260px) rotate(-14deg)' }],
            { duration: 1400, easing: 'ease-in', fill: 'forwards' },
          )
        },
        update: (u) => (this.wind = u * 3),
      })
    }

    /** Whether nothing is queued or playing. */
    get idle() {
      return !this.actions.length
    }

    tick(time, dt) {
      if (!this.still && time - this.lastBoil > 125) {
        this.lastBoil = time
        this.noise.setAttribute('seed', String(1 + (Math.floor(time / 125) % 4)))
      }
      const action = this.actions[0]
      if (action) {
        if (action.began === undefined) {
          action.began = time
          action.start?.()
        }
        const u = this.still ? 1 : Math.min(1, (time - action.began) / action.duration)
        action.update?.(u, time)
        if (u >= 1) this.actions.shift()
      }
      // Every pegged page sits a pull further along for each page hung after it.
      for (let i = 0; i < this.hung; i++) this.pages[i].place(PEG_AT + this.offset - SPACING * i, time, this.wind, this.still ? 0 : dt)
      this.hanger.tick(time, this.still)
      this.dilly.tick(time, dt, this.still)
    }
  }

  /** The overlay: paper over the page while it loads, the scene on it, and the gust it leaves on. */
  class Loader {
    constructor() {
      this.still = matchMedia('(prefers-reduced-motion: reduce)').matches
      this.started = performance.now()
      this.arrivals = new Arrivals()
      this.target = 0
      this.finishing = false
      this.ending = false
      // The scene is played through once a session; after that the paper only waits for the page.
      try {
        this.seen = sessionStorage.getItem('loader') === 'played'
      } catch {
        this.seen = false
      }

      const style = document.createElement('style')
      style.textContent = `
html:has(#loader>.ldr-paper){overflow:hidden}
#loader{position:fixed;inset:0;z-index:2147483647}
#loader .ldr-paper{position:absolute;inset:0;background:${PAPER};transform-origin:50% 0}
#loader svg{position:absolute;left:50%;top:50%;width:min(96vw,1000px,150vh);height:auto;transform:translate(-50%,-50%);opacity:0;animation:ldr-in .3s ${QUICK}ms ease-out forwards}
#loader .ldr-peg{transform-box:fill-box;transform-origin:center}
@media (max-aspect-ratio:3/4){#loader svg{width:118vw}}
@keyframes ldr-in{to{opacity:1}}`
      document.head.appendChild(style)
      this.style = style

      root.setAttribute('role', 'progressbar')
      root.setAttribute('aria-label', 'Loading')
      this.paper = document.createElement('div')
      this.paper.className = 'ldr-paper'
      root.appendChild(this.paper)
      const svg = element('svg', { viewBox: '0 0 800 520', 'aria-hidden': 'true' }, this.paper)
      this.scene = new Scene(svg, this.still)
      // Played already this session: every page is up and coloured, and he and Dilly wait beside them, coloured too.
      if (this.seen) {
        const { scene } = this
        scene.still = true
        for (let i = 0; i < PAGES.length; i++) scene.hangNext(true)
        while (!scene.idle) scene.tick(0, 0)
        scene.hanger.colour(0)
        scene.still = this.still
      }

      this.lastTake = -Infinity
      this.last = performance.now()
      this.frame = requestAnimationFrame((now) => this.tick(now))
    }

    tick(now) {
      // The page's own start-up can hold the frames back a good while; the scene keeps to the clock, not the frames.
      const dt = Math.min(now - this.last, 500) / 1000
      this.last = now
      const age = now - this.started

      if (now - this.lastTake > 200) {
        this.lastTake = now
        // The small pictures come in first and the large ones last, so how many are in says little of how long is
        // left. The pages go up at a pace that slows as it goes, and the pictures that are in can only hurry it.
        const share = this.arrivals.take()
        const patience = 1 - Math.exp(-age / PATIENCE)
        this.target = Math.max(this.target, Math.min(1, Math.max(patience, share * 0.6)))
        root.setAttribute('aria-valuenow', String(Math.round(this.target * 100)))
        if (!this.finishing && (this.arrivals.settled(now) || age > GIVE_UP)) {
          // In before the scene was shown, or played already this session: the paper is just lifted.
          if (age < QUICK || this.seen) return this.leave(false)
          this.finishing = true
        }
      }

      // A page goes up for each sixth of the way; once everything is in, the rest go up quickly and the wind comes.
      const { scene } = this
      if (scene.idle) {
        if (scene.queued < PAGES.length && (this.finishing || this.target >= (scene.queued + 1) / (PAGES.length + 1))) scene.hangNext(this.finishing)
        else if (this.finishing && scene.hung === PAGES.length && !this.ending) {
          this.ending = true
          scene.finish()
        }
      }
      scene.tick(now, dt)
      if (this.ending && scene.idle) return this.leave(!this.still)
      this.frame = requestAnimationFrame((next) => this.tick(next))
    }

    /** Takes the paper away: blown off the page by the gust if `blown`, or lifted plainly. */
    leave(blown) {
      const done = () => {
        cancelAnimationFrame(this.frame)
        root.replaceChildren()
        root.removeAttribute('role')
        root.removeAttribute('aria-label')
        root.removeAttribute('aria-valuenow')
        this.style.remove()
      }
      if (!blown) {
        cancelAnimationFrame(this.frame)
        this.paper.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 220, easing: 'ease-in', fill: 'forwards' })
        return setTimeout(done, 240)
      }
      try {
        sessionStorage.setItem('loader', 'played')
      } catch {}
      root.style.pointerEvents = 'none'
      // The gust keeps the pages flying while the sheet goes: it lifts, curls a little, and is carried up and away.
      const gust = (now) => {
        this.scene.wind = 4
        this.scene.tick(now, Math.min(now - this.last, 500) / 1000)
        this.last = now
        this.frame = requestAnimationFrame(gust)
      }
      this.frame = requestAnimationFrame(gust)
      this.paper.animate(
        [
          { transform: 'translate(0,0) rotate(0) skewY(0)' },
          { transform: 'translate(2vw,-8vh) rotate(-2deg) skewY(-1deg)', offset: 0.3 },
          { transform: 'translate(10vw,-115vh) rotate(-9deg) skewY(-3deg)' },
        ],
        { duration: 1150, easing: 'cubic-bezier(.55,0,.75,.2)', fill: 'forwards' },
      )
      setTimeout(done, 1200)
    }
  }

  new Loader()
})()
