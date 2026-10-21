// The loader, run inline at the top of the body so it is drawn before the bundle, the fonts or a single picture
// arrive. It is drawn and moved the way Dan Yaccarino's Oswald is: flat shapes in clear colours with no outlines, each
// turned a shade darker along one edge, dot eyes and a thin smile, soft shadows on the grass, rolling hills under a
// pale sky, and slow, eased movement that settles. Anurag stands at a pulley clothesline hanging the site's pages
// out to dry as their pictures come in, the badge, the letter, the poster, the mat and the ticket, while Dilly, his
// cat, sits and watches. Once everything is in, the two of them hop for joy, a gust comes, and the sheet blows off
// the page. A classic script, not a module: no imports, nothing left on window.
;(() => {
  const root = document.getElementById('loader')
  if (!root) return

  const SVG = 'http://www.w3.org/2000/svg'
  // The sky, the hills and the grass, and the shade every shape takes along its lower right edge.
  const SKY = '#d3e8f1'
  const CLOUD = '#ffffff'
  const SUN = '#ffd83a'
  const FAR = '#9bd67a'
  const NEAR = '#82c95e'
  const GRASS = '#6dbd4b'
  const BLADE = '#4f9d36'
  const LEAF = '#46a547'
  const BARK = '#8b5a36'
  const SHADE = 'rgba(22,26,70,.17)'
  const SHADOW = 'rgba(28,70,20,.2)'
  const DARK = '#23263f'
  // Anurag, Dilly and the things they use.
  const SKIN = '#c78a5f'
  const HAIR = '#1f1d1d'
  const SHIRT = '#de4a3c'
  const SLEEVE = '#b93a2e'
  const TROUSERS = '#3b52c9'
  const LEG = '#2f42a6'
  const WHITE = '#fdfcf8'
  const GINGER = '#f08a2c'
  const PINK = '#f3a3a0'
  const BLUSH = '#f7c2bb'
  const RED = '#e2473b'
  const BLUE = '#4f7fe3'
  const PLUM = '#7d4c9e'
  const GREEN = '#2f9a5e'
  const YELLOW = '#ffd23f'
  const WOOD = '#e4b46e'
  const WICKER = '#d69a55'
  const METAL = '#a9adbd'
  const ROPE = '#b08b3e'
  // A page in by this is from the cache, and the paper is lifted straight off without the scene being played.
  const QUICK = 250
  // How long the pegging takes to get most of the way when nothing is known of what is still to come, in ms.
  const PATIENCE = 9000
  // Past this the page is shown as it is, so a request that never ends cannot hold it shut.
  const GIVE_UP = 120000

  // Capitals and a few small letters written with one round pen, about ten wide and sixteen tall.
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
  // shape and colour, the colours laid on it, and its marks, drawn a shade darker than what they lie on.
  const PAGES = [
    {
      // The badge: the card in its holder, its photo and its lines.
      width: 60,
      shape: 'M-30 4Q-30 0-26 0H26Q30 0 30 4V80Q30 84 26 84H-26Q-30 84-30 80Z',
      colour: YELLOW,
      fills: [['M-14 24H14V48H-14Z', BLUE], ['M-5 34A5 5 0 1 0 5 34A5 5 0 1 0-5 34ZM-9 48C-8 41 8 41 9 48Z', '#c9d8fb']],
      marks: 'M-9 10H9Q12 10 12 13T9 16H-9Q-12 16-12 13T-9 10ZM-20 58C-12 56-4 60 4 58S16 56 20 58M-20 66C-10 64 0 68 10 66M-20 74C-14 72-8 76 0 74',
    },
    {
      // The letter on handmade paper, its bottom edge deckled, written over in a loose hand and signed.
      width: 64,
      shape: 'M-32 0H32V82C28 86 26 80 22 84S14 82 10 85 2 81-2 84-10 81-14 85-22 81-26 84-30 82-32 83Z',
      colour: BLUE,
      fills: [],
      marks: 'M-24 14c3-5 5 5 8 0s5 5 8 0 5 5 8 0 5 5 8 0 5 5 8 0M-24 26c3-5 5 5 8 0s5 5 8 0 5 5 8 0 5 5 8 0M-24 38c3-5 5 5 8 0s5 5 8 0 5 5 8 0 5 5 8 0 5 5 8 0M-24 50c3-5 5 5 8 0s5 5 8 0 5 5 8 0M2 68c4-8 8 4 4 6s6-10 10-2 4 2 8 0',
    },
    {
      // The poster: a block of flats at night under the moon, a few of its windows lit.
      width: 68,
      shape: 'M-34 0H34V94H-34Z',
      colour: PLUM,
      fills: [
        ['M-22 94V34L0 22 22 34V94Z', '#5f3880'],
        ['M-26 16A6 6 0 1 0-14 16A6 6 0 1 0-26 16ZM-15 40h8v9h-8zM7 40h8v9h-8zM-4 54h8v9h-8zM-15 68h8v9h-8z', YELLOW],
        ['M-4 40h8v9h-8zM-15 54h8v9h-8zM7 54h8v9h-8zM-4 68h8v9h-8zM7 68h8v9h-8zM-4 94V84h8v10Z', '#4a2a66'],
      ],
      marks: '',
    },
    {
      // The cutting mat with its grid, a record and a watch lying on it.
      width: 76,
      shape: 'M-38 0H38V76H-38Z',
      colour: GREEN,
      fills: [
        ['M-27 42A17 17 0 1 0 7 42A17 17 0 1 0-27 42Z', DARK],
        ['M-15 42A5 5 0 1 0-5 42A5 5 0 1 0-15 42Z', RED],
        ['M19 40H25V76H19Z', '#1f6e41'],
        ['M15 58A7 7 0 1 0 29 58A7 7 0 1 0 15 58Z', WHITE],
      ],
      marks: 'M-38 19H38M-38 38H38M-38 57H38M-19 0V76M0 0V76M19 0V76M22 58L24.5 55',
    },
    {
      // The ticket off a roll, notched at its sides, its stub on a perforation, a star stamped on it.
      width: 84,
      shape: 'M-42 0H42V16A6 6 0 0 0 42 28V44H-42V28A6 6 0 0 0-42 16Z',
      colour: RED,
      fills: [['M31 14L33.5 19.5 39 20 35 24 36.5 29.5 31 26.5 25.5 29.5 27 24 23 20 28.5 19.5Z', YELLOW]],
      marks: 'M20 3V7M20 11V15M20 19V23M20 27V31M20 35V39M-32 12H8M-32 20C-24 18-16 22-8 20S4 18 8 20M-32 30H-4M-32 37H0',
    },
  ]

  // Where he pegs, and how far one pull of the line carries the pages along it.
  const PEG_AT = 340
  const SPACING = 84
  // The two runs of the pulley line, from the wheel on the pole to the wheel on the tree.
  const UPPER = [104, 172, 400, 200, 696, 186]
  const LOWER = [104, 196, 400, 226, 696, 208]

  // Anurag, side on, facing the line: a mop of black curls, a big nose. His arms are his sleeves, ending in his
  // hands; each pose is where they reach, every one the same four points so he can be eased from one to the next.
  const POSES = {
    rest: ['M178 324C168 352 168 378 172 400', 'M226 324C238 350 240 374 236 398'],
    up: ['M178 324C186 280 260 230 316 206', 'M226 324C262 290 318 236 364 206'],
    pull: ['M178 324C184 290 232 240 256 214', 'M226 324C252 292 282 248 296 216'],
    over: ['M178 324C184 290 216 240 240 212', 'M226 324C254 292 274 246 282 214'],
  }
  const BODY = {
    feet: [204, 472],
    legs: ['M186 398C186 424 187 446 187 461', 'M220 398C226 424 230 446 233 461'],
    hips: 'M167 390H241L239 412H169Z',
    shoes: 'M172 471C171 461 187 458 194 462 202 464 206 470 202 472H174ZM222 471C221 461 237 458 244 462 252 464 256 470 252 472H224Z',
    torso: 'M165 394C161 368 161 342 168 322 174 308 190 302 204 302S234 306 240 322C246 342 246 368 243 394Z',
    neck: 'M195 303L204 316 213 303Z',
    pocket: 'M220 336H234V347H220Z',
    head: 'M190 292C172 288 162 270 166 250 170 228 190 216 210 218 224 220 232 230 234 244 242 248 252 254 252 262S244 270 236 268C234 280 224 292 206 294Z',
    hair: 'M234 230C242 220 234 206 222 210 222 198 206 193 199 202 194 191 177 194 177 205 164 200 154 213 161 222 148 226 151 242 159 245 148 254 155 268 165 266 162 278 175 283 182 276L186 268C186 258 188 248 194 242 206 234 220 232 234 230Z',
    ear: 'M195 249C186 249 186 264 195 264Z',
    face: 'M215 239Q221 236 227 239M229 281Q233 283 237 280',
    eye: [222, 249],
  }

  // What he stands in: the pole with its wheel, the tree with its wheel, a bird on the pole.
  const POST = { pole: 'M99 172H109V472H99Z', bracket: 'M96 158H112V164H96ZM99 164H103V174H99ZM105 164H109V174H105Z', wheel: [104, 184] }
  const TREE = {
    trunk: 'M692 472C695 400 688 320 692 196H712C716 320 709 400 712 472Z',
    branch: 'M710 300C724 292 732 284 736 272',
    crown: [[652, 128, 44], [700, 86, 50], [752, 116, 44], [698, 140, 52], [744, 152, 36], [664, 160, 34]],
    wheel: [696, 197],
  }
  const BIRD = {
    body: 'M92 150C92 140 102 134 112 138 118 140 120 146 118 150 114 154 96 156 92 150Z',
    tail: 'M92 148L82 142 84 152Z',
    beak: 'M118 142L126 144 118 146Z',
    legs: 'M102 154V160M108 154V160',
    wing: ['M98 146C102 151 108 151 112 146Z', 'M100 146C98 132 110 130 112 146Z'],
    eye: [113, 142],
  }

  // Behind him, the far hills with Big City's pastel blocks just showing over them, three little trees, and the near
  // hill; the grass he stands on runs to the edges of the screen, and so does the sky.
  const HORIZON = [
    'M24 384C70 356 130 348 190 362S300 352 360 344 470 330 540 342 650 334 700 344 760 352 784 348',
    'M24 414C80 392 170 390 240 404S340 420 400 448C420 458 440 466 460 472',
    'M24 474C140 469 260 477 400 472S640 476 784 470',
  ]
  // Each block: its left, its width, its height and its colour, and whether it has a dome.
  const CITY = [[478, 24, 40, '#b99ce3', true], [506, 22, 58, '#8eb2ec', false], [532, 30, 36, '#f5d06b', true], [566, 20, 50, '#c7a3e8', false], [590, 26, 30, '#f2a7b5', false]]
  const FAR_TREES = [[300, 352], [380, 345], [640, 338]]
  const BLADES = [[60, 392], [140, 380], [300, 380], [340, 374], [620, 362], [664, 354], [744, 368], [70, 444], [110, 430], [262, 444], [292, 436], [40, 488], [180, 496], [290, 484], [520, 492], [660, 486], [740, 500]]
  const DAISIES = [[64, 494], [146, 506], [252, 490], [432, 504], [556, 500], [616, 492], [700, 508], [772, 496]]
  const CLOUDS = [[548, 92, 1], [250, 26, 0.6], [770, 236, 0.7]]
  const SUN_AT = [430, 74]
  const PLANE = { trail: 'M262 150C286 118 318 168 338 146', body: 'M346 144L392 134 360 156Z', fold: 'M360 156L364 145 392 134 368 150Z' }
  const BIRDS = 'M466 118q4-5 8 0q4-5 8 0M488 104q3-4 6 0q3-4 6 0'
  // On the grass, a flowering bush by the pole, his mug by the basket, a flower, and a watering can by the tree.
  const BUSH = { shape: 'M28 472C22 460 28 446 40 448 40 436 56 432 62 442 68 432 84 436 84 448 94 450 96 466 92 472Z', flowers: [[46, 452, RED], [66, 444, YELLOW], [80, 460, RED]] }
  const BASKET = { rim: 'M316 430H404V437H316Z', body: 'M320 437H400L392 472H328Z', weave: 'M324 449H396M326 461H394M340 437L344 472M360 437V472M380 437L376 472' }
  const MUG = { body: 'M410 456H426V472H410Z', handle: 'M426 460C433 460 433 468 426 468', steam: 'M415 450C412 446 418 443 415 438M421 450C418 446 424 443 421 438' }
  const FLOWER = { stem: 'M608 472C609 456 606 446 610 436', leaf: 'M610 452C616 444 626 446 626 452 620 456 614 455 610 452Z', head: [610, 430] }
  const CAN = { body: 'M728 452Q728 448 732 448H752Q756 448 756 452V472H728Z', spout: 'M754 462L772 444', rose: [774, 442], handle: 'M732 448C730 434 754 434 752 448' }
  // The shadows on the grass: where, and how wide each way. His and Dilly's shrink as they leave the ground.
  const SHADOWS = [[62, 473, 38, 4], [104, 473, 14, 3], [360, 474, 50, 5], [418, 473, 11, 2.5], [702, 473, 34, 5], [744, 473, 22, 3.5]]
  const FEET = [[208, 474, 54, 6], [474, 474, 38, 5]]

  // Dilly, his cat, a long-haired Turkish Van sat by the basket, facing out: a big round head on a small body, dot
  // eyes and a little mouth, with her markings, a ginger cap over her head and ears parted by a white blaze that runs
  // to a point a little to her right, pale pink in her ears, a ginger moustache either side of her nose, larger on her
  // left, and a plume of a tail, solid ginger. Drawn about the ground under her; her head turns about her neck.
  const DILLY = {
    at: [470, 472],
    size: 1.25,
    tail: 'M22-3C38-1 48-12 46-28C45-36 40-42 36-40 38-32 38-24 33-17 30-13 26-12 22-13Z',
    body: 'M-16-44C-24-36-26-16-24 0H24C26-16 24-36 16-44Z',
    legs: 'M-4-16V-1M4-16V-1M-14 0C-14-5-5-6-4 0M4 0C5-6 14-5 14 0',
    ears: 'M-24-68L-27-97Q-26.5-101-23-99L-5-82ZM24-68L27-97Q26.5-101 23-99L5-82Z',
    inner: 'M-21-73L-23-93-11-82ZM21-73L23-93 11-82Z',
    head: 'M-27-60C-28-74-18-84 0-84S28-74 27-60C26-48 14-41 0-41S-26-48-27-60Z',
    cap: 'M-2-84C-14-84-27-77-27-63-21-68-13-69-5-68ZM-2-84C14-84.5 27-77 27-63 21-68 13-69 5-68Z',
    patches: 'M1-53C3.5-55 8-54.5 8.5-52 8-49.5 4-49 1-50.5ZM-2-53C-4.5-55-8.5-54.5-9-52-8.5-49.5-4.5-49.5-2.5-51Z',
    cheeks: [[-18, -52], [18, -52]],
    mouth: 'M0-52.5V-51M-4-49.5Q-2-47.5 0-51Q2-47.5 4-49.5',
    whiskers: 'M-15-54L-27-56M-15-51L-27-50M15-54L27-56M15-51L27-50',
    nose: 'M-3-55.5H3Q3-54 0-52.5-3-54-3-55.5Z',
    eyes: [-11, 11],
  }
  // Where she looks: how far her eyes shift and the tilt of her head, in degrees.
  const GAZES = { ahead: [0, 0, 4], him: [-2, -0.4, -6], line: [-1.4, -1.6, -10], bird: [-1.8, -1.8, -14] }

  /** A seeded random, so the scene is laid out the same on every visit. */
  const random = (seed) => () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  const ease = (u) => (u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2)
  const glide = (u) => 0.5 - Math.cos(Math.PI * u) / 2

  const element = (name, attributes, parent) => {
    const node = document.createElementNS(SVG, name)
    for (const key in attributes) node.setAttribute(key, attributes[key])
    if (parent) parent.appendChild(node)
    return node
  }
  const stroke = (d, colour, width, parent) =>
    element('path', { d, fill: 'none', stroke: colour, 'stroke-width': width, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, parent)
  const circle = (x, y, r) => `M${x - r} ${y}A${r} ${r} 0 1 0 ${x + r} ${y}A${r} ${r} 0 1 0 ${x - r} ${y}Z`

  let shades = 0
  /** Darkens a shape along its lower right edge, where it turns from the light: the shape less itself moved up and left. */
  const shade = (d, parent, depth = 3) => {
    const id = `ldr-shade-${shades++}`
    const mask = element('mask', { id }, parent)
    element('path', { d, fill: '#fff' }, mask)
    element('path', { d, fill: '#000', transform: `translate(${-depth} ${(-depth * 0.7).toFixed(2)})` }, mask)
    return element('path', { d, fill: SHADE, mask: `url(#${id})` }, parent)
  }
  /** A flat shape in one colour with no outline, shaded along one edge. */
  const solid = (d, colour, parent, depth = 3) => {
    const shape = element('path', { d, fill: colour }, parent)
    if (depth) shade(d, parent, depth)
    return shape
  }

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

  /**
   * A hop for joy, `u` of the way through: down into a squash, up stretched, down again, and a little squash on
   * landing. How far up it is, and how much wider and taller than usual.
   */
  const hop = (u) => {
    if (u <= 0 || u >= 1) return [0, 1, 1]
    if (u < 0.15) {
      const s = glide(u / 0.15)
      return [0, 1 + s * 0.06, 1 - s * 0.08]
    }
    if (u < 0.5) {
      const s = 1 - (1 - (u - 0.15) / 0.35) ** 2
      return [-22 * s, 1.06 - s * 0.09, 0.92 + s * 0.14]
    }
    if (u < 0.82) {
      const s = ((u - 0.5) / 0.32) ** 2
      return [-22 * (1 - s), 0.97 + s * 0.02, 1.06 - s * 0.06]
    }
    const s = Math.sin(((u - 0.82) / 0.18) * Math.PI)
    return [0, 1 + s * 0.05, 1 - s * 0.06]
  }

  /** One of the site's pages, hung by two pegs, swinging on the line. */
  class Page {
    constructor(parent, spec, index) {
      this.seed = index * 1.7
      this.angle = 0
      this.spin = 0
      this.lift = 0
      this.group = element('g', { visibility: 'hidden' }, parent)
      solid(spec.shape, spec.colour, this.group)
      for (const [d, colour] of spec.fills) element('path', { d, fill: colour }, this.group)
      if (spec.marks) stroke(spec.marks, SHADE, 2.2, this.group)
      // The pegs, sprung shut over the line.
      this.pegs = [-1, 1].map((side) => {
        const peg = element('g', { transform: `translate(${side * (spec.width / 2 - 9)} 0)` }, this.group)
        const inner = element('g', { class: 'ldr-peg' }, peg)
        solid('M-3.5-9H3.5V9H-3.5Z', WOOD, inner, 1.6)
        element('path', { d: 'M-3.5-0.8H3.5V0.8H-3.5Z', fill: '#9aa0ad' }, inner)
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

  /** Anurag: his sleeves and hands eased from pose to pose, his breathing, a blink now and then, and a hop at the end. */
  class Hanger {
    constructor(parent) {
      const group = element('g', {}, parent)
      this.group = group
      const hand = (colour) => element('circle', { r: 6.5, fill: colour }, group)
      this.back = stroke(POSES.rest[0], SLEEVE, 12, group)
      this.backHand = hand('#ad7550')
      stroke(BODY.legs[0], LEG, 17, group)
      stroke(BODY.legs[1], TROUSERS, 17, group)
      element('path', { d: BODY.shoes, fill: DARK }, group)
      solid(BODY.hips, TROUSERS, group)
      solid(BODY.torso, SHIRT, group, 4)
      element('path', { d: BODY.neck, fill: SKIN }, group)
      element('path', { d: BODY.pocket, fill: SLEEVE }, group)
      solid(BODY.head, SKIN, group, 4)
      element('path', { d: BODY.hair, fill: HAIR }, group)
      element('path', { d: BODY.ear, fill: '#ad7550' }, group)
      stroke(BODY.face, DARK, 2.2, group)
      const [ex, ey] = BODY.eye
      this.eye = element('circle', { cx: ex, cy: ey, r: 3, fill: DARK }, group)
      this.lid = stroke(`M${ex - 3.5} ${ey + 0.5}H${ex + 3.5}`, DARK, 2.2, group)
      this.lid.setAttribute('visibility', 'hidden')
      this.front = stroke(POSES.rest[1], SHIRT, 12, group)
      this.frontHand = hand(SKIN)
      this.now = this.reach('rest')
      this.pose('rest', true)
      this.nextBlink = 1800
      this.hopping = 0
    }

    /** The numbers of the two arms in pose `name`. */
    reach(name) {
      return POSES[name].map((d) => d.match(/-?[\d.]+/g).map(Number))
    }

    /** Eases his arms to `name`, or puts them there at once if `snap`. */
    pose(name, snap) {
      if (this.current === name && !snap) return
      this.current = name
      this.from = this.now
      this.to = this.reach(name)
      this.began = snap ? -Infinity : null
    }

    tick(time, still) {
      if (this.began === null) this.began = time
      const k = glide(still ? 1 : Math.min(1, (time - this.began) / 170))
      this.now = this.to.map((arm, a) => arm.map((n, i) => this.from[a][i] + (n - this.from[a][i]) * k))
      for (const [sleeve, hand, n] of [[this.back, this.backHand, this.now[0]], [this.front, this.frontHand, this.now[1]]]) {
        const p = n.map((v) => v.toFixed(1))
        sleeve.setAttribute('d', `M${p[0]} ${p[1]}C${p[2]} ${p[3]} ${p[4]} ${p[5]} ${p[6]} ${p[7]}`)
        hand.setAttribute('cx', p[6])
        hand.setAttribute('cy', p[7])
      }
      if (still) return
      // He breathes from his feet up, and hops from them.
      const [x, y] = BODY.feet
      const [dy, sx, sy] = hop(this.hopping)
      const breath = 1 + Math.sin(time / 700) * 0.007
      this.group.setAttribute('transform', `translate(${x} ${(y + dy).toFixed(2)}) scale(${sx.toFixed(4)} ${(sy * breath).toFixed(4)}) translate(${-x} ${-y})`)
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
    constructor(parent) {
      this.group = element('g', {}, parent)
      this.tail = element('g', {}, this.group)
      solid(DILLY.tail, GINGER, this.tail, 2.4)
      solid(DILLY.body, WHITE, this.group)
      stroke(DILLY.legs, '#d9dbe6', 1.6, this.group)
      this.head = element('g', {}, this.group)
      solid(DILLY.ears, GINGER, this.head, 2)
      element('path', { d: DILLY.inner, fill: BLUSH }, this.head)
      element('path', { d: DILLY.head, fill: WHITE }, this.head)
      element('path', { d: DILLY.cap, fill: GINGER }, this.head)
      shade(DILLY.head, this.head)
      for (const [cx, cy] of DILLY.cheeks) element('ellipse', { cx, cy, rx: 4, ry: 2.4, fill: BLUSH }, this.head)
      element('path', { d: DILLY.patches, fill: GINGER }, this.head)
      element('path', { d: DILLY.nose, fill: PINK }, this.head)
      stroke(DILLY.mouth, DARK, 1.6, this.head)
      stroke(DILLY.whiskers, '#8c90a6', 1, this.head)
      this.eyes = element('g', {}, this.head)
      this.pupils = DILLY.eyes.map((x) => {
        const eye = element('g', {}, element('g', { transform: `translate(${x} -62)` }, this.eyes))
        element('ellipse', { rx: 2.5, ry: 3.2, fill: DARK }, eye)
        return eye
      })
      // Shut, her eyes are happy little arches.
      this.lids = stroke(DILLY.eyes.map((x) => `M${x - 3.5} -61Q${x} -65.5 ${x + 3.5} -61`).join(''), DARK, 2, this.head)
      this.lids.setAttribute('visibility', 'hidden')
      this.place(0)

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
      this.hopping = 0
    }

    /** Sets her on the grass, `hopping` of the way through a hop. */
    place(hopping) {
      const [dy, sx, sy] = hop(hopping)
      const [x, y] = DILLY.at
      this.group.setAttribute('transform', `translate(${x} ${(y + dy).toFixed(2)}) scale(${(DILLY.size * sx).toFixed(4)} ${(DILLY.size * sy).toFixed(4)})`)
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
      this.place(this.hopping)
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

  /** The scene: the sky and hills, the caption, Anurag, Dilly, his basket and the pages, and what they do next. */
  class Scene {
    constructor(svg, still) {
      this.still = still
      const rand = random(11)
      const back = element('g', {}, svg)
      // The sky and the grass run on past the drawing to the edges of the screen, whatever its shape.
      element('path', { d: 'M-4000-4000H4800V600H-4000Z', fill: SKY }, back)
      const [sx, sy] = SUN_AT
      this.sun = element('path', { d: circle(sx, sy, 30), fill: '#fff3b0', opacity: 0.6 }, back)
      solid(circle(sx, sy, 20), SUN, back, 2.4)
      this.clouds = CLOUDS.map(([x, y, size]) => {
        const cloud = element('g', {}, back)
        const puff = element('g', { transform: `translate(${x} ${y}) scale(${size})` }, cloud)
        solid('M-44 18C-58 18-60 0-44-2-44-18-22-24-12-12-4-28 22-26 26-10 42-14 52 4 40 18Z', CLOUD, puff)
        return { cloud, phase: x / 90 }
      })
      this.plane = element('g', {}, back)
      stroke(PLANE.trail, CLOUD, 2, this.plane).setAttribute('stroke-dasharray', '3 6')
      solid(PLANE.body, WHITE, this.plane, 2)
      element('path', { d: PLANE.fold, fill: '#dfe3ee' }, this.plane)
      stroke(BIRDS, DARK, 1.8, back)

      // Big City over the far hill, then the hills from the back forward.
      for (const [x, w, h, colour, dome] of CITY) {
        const top = 346 - h
        if (dome) solid(circle(x + w / 2, top, w / 2 - 3), colour, back, 2)
        solid(`M${x} ${top}H${x + w}V350H${x}Z`, colour, back, 2)
        let windows = ''
        for (let row = top + 6; row < 340; row += 9) for (let col = x + 4; col + 4 <= x + w - 3; col += 7) windows += `M${col} ${row}h4v5h-4z`
        element('path', { d: windows, fill: CLOUD, opacity: 0.7 }, back)
      }
      const [far, near, ground] = HORIZON
      element('path', { d: `M-4000 404H-120C-60 404-10 394 ${far.slice(1)}C840 344 900 354 960 358H4800V600H-4000Z`, fill: FAR }, back)
      for (const [x, y] of FAR_TREES) {
        stroke(`M${x} ${y + 2}V${y - 16}`, BARK, 3, back)
        solid(circle(x, y - 22, 9), LEAF, back, 2)
      }
      element('path', { d: `M-4000 436H-80C-40 434 0 422 ${near.slice(1)}V600H-4000Z`, fill: NEAR }, back)
      element('path', { d: `M-4000 474H24${ground.slice(ground.indexOf('C'))}H4800V4000H-4000Z`, fill: GRASS }, back)
      element('path', { d: BLADES.map(([x, y]) => `M${x - 2.5} ${y}l2.5-7 2.5 7Z`).join(''), fill: BLADE }, back)
      for (const [x, y] of DAISIES) {
        let petals = ''
        for (let i = 0; i < 5; i++) petals += circle(+(x + Math.cos(i * 1.257) * 3).toFixed(1), +(y + Math.sin(i * 1.257) * 3).toFixed(1), 2.4)
        element('path', { d: petals, fill: WHITE }, back)
        element('circle', { cx: x, cy: y, r: 1.8, fill: SUN }, back)
      }
      for (const [x, y, rx, ry] of SHADOWS) element('ellipse', { cx: x, cy: y, rx, ry, fill: SHADOW }, back)
      this.feet = FEET.map(([x, y, rx, ry]) => element('ellipse', { cx: x, cy: y, rx, ry, fill: SHADOW }, back))

      // The pole, the tree and the line between them.
      solid(POST.pole, METAL, back)
      solid(POST.bracket, METAL, back, 1.6)
      const wheel = ([x, y]) => {
        solid(circle(x, y, 11), '#7d8296', back, 2)
        element('circle', { cx: x, cy: y, r: 3, fill: '#4d5163' }, back)
      }
      wheel(POST.wheel)
      solid(TREE.trunk, BARK, back, 4)
      stroke(TREE.branch, BARK, 7, back)
      this.crown = element('g', {}, back)
      for (const [x, y, r] of TREE.crown) solid(circle(x, y, r), LEAF, this.crown, 5)
      for (let i = 0; i < 9; i++) {
        const a = rand() * Math.PI * 2
        const r = Math.sqrt(rand()) * 52
        element('circle', { cx: (704 + Math.cos(a) * r * 1.1).toFixed(1), cy: (114 + Math.sin(a) * r * 0.85).toFixed(1), r: 4.5, fill: RED }, this.crown)
      }
      wheel(TREE.wheel)
      stroke(`M${UPPER[0]} ${UPPER[1]}Q${UPPER.slice(2).join(' ')}M${LOWER[0]} ${LOWER[1]}Q${LOWER.slice(2).join(' ')}`, ROPE, 1.8, back)
      this.caption(back)

      // The things on the grass.
      solid(BUSH.shape, LEAF, back, 4)
      for (const [x, y, colour] of BUSH.flowers) solid(circle(x, y, 3.6), colour, back, 1.2)
      solid(BASKET.rim, '#b97f3e', back, 1.6)
      this.sheets = PAGES.map((_, i) => {
        const sheet = element('g', { transform: `translate(${336 + i * 12} 433) rotate(${((rand() - 0.5) * 24).toFixed(1)})` }, back)
        solid('M-11 2V-20H11V2Z', WHITE, sheet, 2)
        return sheet
      })
      solid(BASKET.body, WICKER, back)
      stroke(BASKET.weave, '#b97f3e', 1.8, back)
      stroke(MUG.handle, RED, 3, back)
      solid(MUG.body, RED, back, 2)
      stroke(MUG.steam, CLOUD, 1.6, back).setAttribute('opacity', 0.8)
      stroke(FLOWER.stem, BLADE, 3, back)
      element('path', { d: FLOWER.leaf, fill: BLADE }, back)
      const [fx, fy] = FLOWER.head
      for (let i = 0; i < 5; i++) element('circle', { cx: (fx + Math.cos(i * 1.257 - 1.57) * 5).toFixed(1), cy: (fy + Math.sin(i * 1.257 - 1.57) * 5).toFixed(1), r: 4, fill: '#f27aa0' }, back)
      element('circle', { cx: fx, cy: fy, r: 3, fill: SUN }, back)
      stroke(CAN.handle, BLUE, 3.5, back)
      stroke(CAN.spout, BLUE, 4.5, back)
      solid(circle(...CAN.rose, 4.5), BLUE, back, 1.4)
      solid(CAN.body, BLUE, back)

      this.dilly = new Dilly(svg)
      this.hanger = new Hanger(svg)
      const line = element('g', {}, svg)
      this.pages = PAGES.map((spec, i) => new Page(line, spec, i))
      this.bird = this.perch(svg)

      this.hung = 0
      this.queued = 0
      this.offset = 0
      this.wind = 0
      this.actions = []
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
          stroke(d, '#2f3fc8', 4 / size, g)
          x += (width + 4.5) * size
        }
      }
    }

    /** The bird on the pole, who flies off when the wind gets up. */
    perch(parent) {
      const group = element('g', {}, parent)
      stroke(BIRD.legs, DARK, 1.6, group)
      element('path', { d: BIRD.tail, fill: '#b9352b' }, group)
      solid(BIRD.body, RED, group, 2)
      element('path', { d: BIRD.beak, fill: SUN }, group)
      element('circle', { cx: BIRD.eye[0], cy: BIRD.eye[1], r: 1.8, fill: DARK }, group)
      return { group, wing: element('path', { d: BIRD.wing[0], fill: '#b9352b' }, group) }
    }

    /** Queues the next page: pull the line along, lift the page up to it and peg it. */
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
            this.hanger.pose(u < 1 && Math.floor(time / 190) % 2 ? 'pull' : 'over')
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
      this.actions.push({ duration: 600 * k, start: () => this.hanger.pose('rest') })
    }

    /** Queues the end: the two of them hop for joy, the wind gets up and the bird leaves. */
    finish() {
      this.actions.push({
        duration: 900,
        start: () => this.dilly.watch('ahead', 1.5),
        update: (u) => {
          if (this.still) return
          this.hanger.hopping = u
          this.dilly.hopping = Math.max(0, u * 1.15 - 0.15)
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
      if (this.still) return
      // The world keeps moving gently: the clouds drifting, the sun glowing, the plane bobbing, the tree swaying.
      for (const { cloud, phase } of this.clouds) cloud.setAttribute('transform', `translate(${(Math.sin(time / 5200 + phase) * 14).toFixed(2)} 0)`)
      const glow = 1 + Math.sin(time / 800) * 0.06
      this.sun.setAttribute('transform', `translate(${SUN_AT.join(' ')}) scale(${glow.toFixed(4)}) translate(${-SUN_AT[0]} ${-SUN_AT[1]})`)
      this.plane.setAttribute('transform', `translate(0 ${(Math.sin(time / 650) * 4).toFixed(2)}) rotate(${(Math.sin(time / 900) * 2).toFixed(2)} 360 148)`)
      this.crown.setAttribute('transform', `rotate(${(Math.sin(time / 1300) * 0.8 + this.wind * 0.6).toFixed(3)} 702 260)`)
      ;[this.hanger, this.dilly].forEach(({ hopping }, i) => {
        const [x, y] = FEET[i]
        const k = (1 + hop(hopping)[0] / 50).toFixed(3)
        this.feet[i].setAttribute('transform', `translate(${x} ${y}) scale(${k}) translate(${-x} ${-y})`)
      })
    }
  }

  /** The overlay: the scene over the page while it loads, and the gust it leaves on. */
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
#loader .ldr-paper{position:absolute;inset:0;overflow:hidden;background:${SKY};transform-origin:50% 0}
#loader svg{position:absolute;left:50%;top:50%;width:min(96vw,1000px,150vh);height:auto;overflow:visible;transform:translate(-50%,-50%);opacity:0;animation:ldr-in .3s ${QUICK}ms ease-out forwards}
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
      // Played already this session: every page is up, and the two of them wait beside them.
      if (this.seen) {
        const { scene } = this
        scene.still = true
        for (let i = 0; i < PAGES.length; i++) scene.hangNext(true)
        while (!scene.idle) scene.tick(0, 0)
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
