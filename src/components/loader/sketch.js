// The loader, run inline at the top of the body so it is drawn before the bundle, the fonts or a single picture
// arrive. It is drawn and moved the way Dan Yaccarino's Oswald is: flat shapes in clear colours with no outlines, each
// turned a shade darker along one edge, dot eyes and a thin smile, soft shadows on the grass, a cyan sky, Big City's
// street of framed windows with something odd about each building, odd neighbours, and slow, eased movement that
// settles. In a yard across the street from them, Anurag stands at a pulley clothesline hanging the site's pages out to dry as their
// pictures come in, the badge, the letter, the poster, the mat and the ticket, while Dilly, his cat, watches, a
// sunflower on noodle legs waves and a butterfly flits about. Once everything is in, they hop for joy, a gust comes,
// and the sheet blows off the page. A classic script, not a module: no imports, nothing left on window.
;(() => {
  const root = document.getElementById('loader')
  if (!root) return

  const SVG = 'http://www.w3.org/2000/svg'
  // The sky and the grass, and the shade every shape takes along its lower right edge.
  const SKY = '#a6e7ea'
  const CLOUD = '#ffffff'
  const SUN = '#ffd83a'
  const GRASS = '#6dbd4b'
  const BLADE = '#4f9d36'
  const LEAF = '#3fae4a'
  const BARK = '#c27330'
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

  // What he stands in: a curly Big City street lamp with the line's wheel on it, its lantern and a bird on top, and a
  // Big City tree with the other wheel, a crown of two greens with its orange branches drawn over it.
  const LAMP = { post: 'M104 472V190C104 164 132 158 140 176 144 188 134 196 128 190', wire: 'M128 190V194', lantern: 'M121 194H135L132 210H124Z', cap: 'M120 193H136', wheel: [104, 184] }
  const TREE = {
    trunk: 'M690 472C694 400 690 320 694 240L700 200H708L712 240C716 320 712 400 714 472Z',
    crown: 'M612 128C604 92 636 52 680 50 702 30 748 34 762 62 794 70 800 118 784 140 790 170 756 190 724 178 700 196 660 192 642 170 616 166 604 146 612 128Z',
    light: 'M630 110C622 80 650 56 684 60 700 46 732 50 740 70 716 74 700 84 690 100 668 96 650 106 630 110Z',
    branches: 'M702 236C690 200 668 176 644 150M706 222C718 190 738 164 760 138M704 200C702 160 706 120 700 80M664 170L650 132M740 156L756 108',
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

  // Behind the yard, Big City: a warm grey skyline far off, then a street of buildings, each a box with a darker side,
  // framed windows, a door and a step, and here and there something odd about it, as Big City's are: a cheese house,
  // a teacup on the café, a cactus up a wall, a baseball house. Puffy clouds and a hot-air balloon go over.
  const STREET = 390
  const SKYLINE = '#cbc4c2'
  const LAWN = '#7bd152'
  const CLOUDS = [[548, 74, 1], [250, 18, 0.6], [24, 112, 0.55]]
  const BALLOON = [462, 66]
  const GROUND = 'M24 474C140 469 260 477 400 472S640 476 784 470'
  const BLADES = [[40, 488], [180, 496], [290, 484], [520, 492], [660, 486], [740, 500], [150, 452], [272, 446], [604, 450], [452, 446]]
  const DAISIES = [[64, 494], [146, 506], [252, 490], [432, 504], [556, 500], [646, 492], [700, 508], [772, 496]]
  // On the grass, a flowering bush by the lamp, his mug by the basket, and a watering can by the tree.
  const BUSH = { shape: 'M28 472C22 460 28 446 40 448 40 436 56 432 62 442 68 432 84 436 84 448 94 450 96 466 92 472Z', twigs: 'M50 452L45 438M70 448L75 434M84 456L90 446', flowers: [[46, 452, RED], [66, 444, YELLOW], [80, 460, RED]] }
  const BASKET = { rim: 'M316 430H404V437H316Z', body: 'M320 437H400L392 472H328Z', weave: 'M324 449H396M326 461H394M340 437L344 472M360 437V472M380 437L376 472' }
  const MUG = { body: 'M410 456H426V472H410Z', handle: 'M426 460C433 460 433 468 426 468', steam: 'M415 450C412 446 418 443 415 438M421 450C418 446 424 443 421 438' }
  const CAN = { body: 'M728 452Q728 448 732 448H752Q756 448 756 452V472H728Z', spout: 'M754 462L772 444', rose: [774, 442], handle: 'M732 448C730 434 754 434 752 448' }
  // The shadows on the grass: where, and how wide each way. His, Dilly's and the sunflower's shrink as they hop.
  const SHADOWS = [[62, 473, 38, 4], [104, 473, 12, 3], [360, 474, 50, 5], [418, 473, 11, 2.5], [702, 473, 30, 5], [744, 473, 22, 3.5]]
  const FEET = [[208, 474, 54, 6], [474, 474, 38, 5], [566, 474, 18, 3]]

  // A sunflower from the bed by the baseball house, one of Big City's odd neighbours: she stands about on two green noodles of
  // legs with her hands on her hips, sways, and waves when a page goes up. Drawn about the ground under her.
  const SUNFLOWER = {
    at: [566, 472],
    legs: 'M-6 0C-8-20-4-36-2-52M6 0C8-20 4-36 2-52',
    feet: 'M-6 0H-14M6 0H14',
    stem: 'M0-50C-1-72 1-96 0-124',
    leaves: 'M0-96C8-108 20-104 22-98 14-92 6-92 0-96ZM0-66C-8-78-20-74-22-68-14-62-6-62 0-66Z',
    hips: ['M0-84C-11-86-15-74-7-68', 'M0-84C11-86 15-74 7-68'],
    wave: 'M0-84C10-90 16-102 15-114',
    head: [0, -140],
    face: 'M0-141Q2.5-138-.5-136.5M-5-133Q0-129 5-133',
  }
  // A butterfly with a face, out among the pages, her wings opening and shutting as she goes. Drawn about her middle;
  // each wing is the left one, turned over for the right.
  const BUTTERFLY = {
    at: [420, 150],
    upper: 'M0 0C-6-14-22-20-26-10-30 0-16 6 0 2Z',
    lower: 'M0 2C-10 6-18 16-12 20-6 24-2 12 0 4Z',
    spots: [[-17, -8, 3.2], [-9, -3, 2], [-9, 14, 2.2]],
    body: 'M-2.5-6C-2.5-10 2.5-10 2.5-6V12C2.5 16-2.5 16-2.5 12Z',
    feelers: 'M-1-13C-3-19-6-21-8-21M1-13C3-19 6-21 8-21',
  }

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

  /** The sunflower: her sway, her wave when a page goes up, and her hop at the end. */
  class Sunflower {
    constructor(parent) {
      this.group = element('g', {}, parent)
      const body = element('g', {}, this.group)
      this.body = body
      const green = '#3f9a3e'
      stroke(SUNFLOWER.legs, green, 3.2, body)
      stroke(SUNFLOWER.feet, green, 3.2, body)
      stroke(SUNFLOWER.stem, green, 4, body)
      element('path', { d: SUNFLOWER.leaves, fill: green }, body)
      stroke(SUNFLOWER.hips[0], green, 3, body)
      this.hip = stroke(SUNFLOWER.hips[1], green, 3, body)
      this.arm = element('g', { visibility: 'hidden' }, body)
      stroke(SUNFLOWER.wave, green, 3, this.arm)
      this.head = element('g', {}, body)
      const [hx, hy] = SUNFLOWER.head
      for (let i = 0; i < 12; i++) element('ellipse', { cx: hx, cy: hy - 16, rx: 5.5, ry: 10, fill: YELLOW, transform: `rotate(${i * 30} ${hx} ${hy})` }, this.head)
      solid(circle(hx, hy, 15), '#f2b51f', this.head, 0)
      solid(circle(hx, hy, 12), '#c8692d', this.head, 2)
      element('circle', { cx: hx - 4, cy: hy - 2, r: 1.5, fill: DARK }, this.head)
      element('circle', { cx: hx + 4, cy: hy - 2, r: 1.5, fill: DARK }, this.head)
      stroke(SUNFLOWER.face, DARK, 1.6, this.head)
      this.waving = 0
      this.hopping = 0
      this.place(0, 0)
    }

    /** Waves for a little while. */
    wave() {
      this.waving = 1.1
    }

    place(time, hopping) {
      const [x, y] = SUNFLOWER.at
      const [dy, sx, sy] = hop(hopping)
      this.group.setAttribute('transform', `translate(${x} ${(y + dy).toFixed(2)}) scale(${sx.toFixed(4)} ${sy.toFixed(4)})`)
      // She sways from her feet, and her head a little more, a beat behind.
      this.body.setAttribute('transform', `rotate(${(Math.sin(time / 1100) * 2.5).toFixed(2)})`)
      this.head.setAttribute('transform', `rotate(${(Math.sin(time / 1100 - 0.6) * 4).toFixed(2)} 0 -124)`)
    }

    tick(time, dt, still) {
      if (still) return
      this.waving -= dt
      const waving = this.waving > 0
      this.arm.setAttribute('visibility', waving ? 'visible' : 'hidden')
      this.hip.setAttribute('visibility', waving ? 'hidden' : 'visible')
      if (waving) this.arm.setAttribute('transform', `rotate(${(Math.sin(time / 90) * 14).toFixed(2)} 0 -84)`)
      this.place(time, this.hopping)
    }
  }

  /** The butterfly: wandering loops over the line, wings beating, carried off by the gust. */
  class Butterfly {
    constructor(parent) {
      this.group = element('g', {}, parent)
      this.wings = [1, -1].map((side) => {
        const wing = element('g', {}, element('g', { transform: `scale(${side} 1)` }, this.group))
        solid(BUTTERFLY.upper, '#f39a3c', wing, 1.6)
        solid(BUTTERFLY.lower, '#f0812a', wing, 1.2)
        for (const [x, y, r] of BUTTERFLY.spots) element('circle', { cx: x, cy: y, r, fill: RED }, wing)
        return wing
      })
      stroke(BUTTERFLY.feelers, DARK, 1.2, this.group)
      element('path', { d: BUTTERFLY.body, fill: '#e86ab6' }, this.group)
      element('circle', { cx: 0, cy: -10, r: 4.6, fill: '#e86ab6' }, this.group)
      element('circle', { cx: -1.6, cy: -10.5, r: 0.9, fill: DARK }, this.group)
      element('circle', { cx: 1.6, cy: -10.5, r: 0.9, fill: DARK }, this.group)
      this.away = [0, 0]
      this.place(0)
    }

    place(time) {
      const [x, y] = BUTTERFLY.at
      const px = x + Math.sin(time / 2300) * 70 + this.away[0]
      const py = y + Math.sin(time / 1100) * 20 + Math.sin(time / 300) * 4 + this.away[1]
      this.group.setAttribute('transform', `translate(${px.toFixed(2)} ${py.toFixed(2)}) rotate(${(Math.cos(time / 2300) * 10).toFixed(2)})`)
    }

    tick(time, dt, wind, still) {
      if (still) return
      // Her wings shut to edge-on and open again about five times a second.
      const open = (0.25 + 0.75 * Math.abs(Math.cos(time / 32))).toFixed(3)
      for (const wing of this.wings) wing.setAttribute('transform', `scale(${open} 1)`)
      if (wind) {
        this.away[0] += wind * 60 * dt
        this.away[1] -= wind * 40 * dt
      }
      this.place(time)
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
      this.city(back, rand)
      this.clouds = CLOUDS.map(([x, y, size]) => {
        const cloud = element('g', {}, back)
        const puff = element('g', { transform: `translate(${x} ${y}) scale(${size})` }, cloud)
        solid('M-44 18C-58 18-60 0-44-2-44-18-22-24-12-12-4-28 22-26 26-10 42-14 52 4 40 18Z', CLOUD, puff)
        return { cloud, phase: x / 90 }
      })
      this.balloon = element('g', {}, back)
      const lift = element('g', { transform: `translate(${BALLOON.join(' ')})` }, this.balloon)
      solid('M0-22C14-22 22-12 22 0 22 12 10 20 6 26H-6C-10 20-22 12-22 0-22-12-14-22 0-22Z', RED, lift, 2)
      element('path', { d: 'M0-22C6-12 7 10 4 26H-4C-7 10-6-12 0-22Z', fill: YELLOW }, lift)
      stroke('M-6 26L-5 34M6 26L5 34', '#7a5a3a', 1.2, lift)
      solid('M-6 34H6V42H-6Z', WICKER, lift, 1.2)

      element('path', { d: `M-4000 ${STREET + 32}H4800V600H-4000Z`, fill: LAWN }, back)
      // The yard's curly railing, with a flower on every other post.
      let rails = 'M-400 414H1200M-400 428H1200'
      let flowers = ''
      for (let x = -396, i = 0; x < 1200; x += 22, i++) {
        rails += `M${x} 434V414c0-6 7-6 7 0`
        if (i % 2) flowers += `M${x + 3.5} 402v8M${x - 0.5} 406h8`
      }
      stroke(rails, '#2c3a5c', 2, back)
      stroke(flowers, '#f6d43f', 3, back)
      element('path', { d: `M-4000 474H24${GROUND.slice(GROUND.indexOf('C'))}H4800V4000H-4000Z`, fill: GRASS }, back)
      element('path', { d: BLADES.map(([x, y]) => `M${x - 2.5} ${y}l2.5-7 2.5 7Z`).join(''), fill: BLADE }, back)
      for (const [x, y] of DAISIES) {
        let petals = ''
        for (let i = 0; i < 5; i++) petals += circle(+(x + Math.cos(i * 1.257) * 3).toFixed(1), +(y + Math.sin(i * 1.257) * 3).toFixed(1), 2.4)
        element('path', { d: petals, fill: WHITE }, back)
        element('circle', { cx: x, cy: y, r: 1.8, fill: SUN }, back)
      }
      for (const [x, y, rx, ry] of SHADOWS) element('ellipse', { cx: x, cy: y, rx, ry, fill: SHADOW }, back)
      this.feet = FEET.map(([x, y, rx, ry]) => element('ellipse', { cx: x, cy: y, rx, ry, fill: SHADOW }, back))

      // The lamp, the tree and the line between them.
      const wheel = ([x, y]) => {
        solid(circle(x, y, 11), '#7d8296', back, 2)
        element('circle', { cx: x, cy: y, r: 3, fill: '#4d5163' }, back)
      }
      stroke(LAMP.post, '#2c3a5c', 7, back)
      stroke(LAMP.wire, '#2c3a5c', 1.6, back)
      stroke(LAMP.cap, '#2c3a5c', 3, back)
      this.lantern = element('path', { d: LAMP.lantern, fill: '#ffe27a' }, back)
      wheel(LAMP.wheel)
      solid(TREE.trunk, BARK, back, 4)
      this.crown = element('g', {}, back)
      solid(TREE.crown, LEAF, this.crown, 7)
      element('path', { d: TREE.light, fill: '#5cc75a' }, this.crown)
      stroke(TREE.branches, BARK, 5, this.crown)
      wheel(TREE.wheel)
      stroke(`M${UPPER[0]} ${UPPER[1]}Q${UPPER.slice(2).join(' ')}M${LOWER[0]} ${LOWER[1]}Q${LOWER.slice(2).join(' ')}`, ROPE, 1.8, back)
      this.caption(back)

      // The things on the grass.
      solid(BUSH.shape, LEAF, back, 4)
      stroke(BUSH.twigs, BARK, 3, back)
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
      stroke(CAN.handle, BLUE, 3.5, back)
      stroke(CAN.spout, BLUE, 4.5, back)
      solid(circle(...CAN.rose, 4.5), BLUE, back, 1.4)
      solid(CAN.body, BLUE, back)

      this.sunflower = new Sunflower(svg)
      this.dilly = new Dilly(svg)
      this.hanger = new Hanger(svg)
      const line = element('g', {}, svg)
      this.pages = PAGES.map((spec, i) => new Page(line, spec, i))
      this.bird = this.perch(svg)
      this.butterfly = new Butterfly(svg)

      this.hung = 0
      this.queued = 0
      this.offset = 0
      this.wind = 0
      this.actions = []
    }

    /**
     * Big City along the far side of the street: the skyline far off, then the buildings left to right, plain blocks
     * at the edges, the cheese house, an olive apartment block, a teal one with arched windows, the café with a teacup
     * on its roof, a green block with a cactus up its wall, the baseball house, and a lilac tower behind the tree.
     */
    city(parent, rand) {
      const flat = (d, colour) => element('path', { d, fill: colour }, parent)
      const paint = (d, colour, depth = 2.4) => solid(d, colour, parent, depth)
      const line = (d, colour, width) => stroke(d, colour, width, parent)
      const rect = (x, y, w, h) => `M${x} ${y}h${w}v${h}h${-w}z`
      // A shape in a colour, darker by `dark` (a side in shadow, a cornice).
      const toned = (d, colour, dark) => {
        flat(d, colour)
        element('path', { d, fill: `rgba(22,26,70,${dark})` }, parent)
      }

      let blocks = ''
      let dots = ''
      for (let x = -900; x < 1700; ) {
        const w = 30 + Math.floor(rand() * 40)
        const top = STREET - 130 - Math.floor(rand() * 90)
        blocks += rect(x, top, w, STREET - top)
        if (rand() < 0.5) blocks += rect(x + 6, top - 10, Math.floor(w / 2), 10)
        for (let i = 0; i < 3; i++) if (rand() < 0.7) dots += rect(x + 6 + Math.floor(rand() * (w - 14)), top + 12 + Math.floor(rand() * 60), 6, 7)
        x += w
      }
      flat(blocks, SKYLINE)
      flat(dots, '#b3aba9')

      /** A building: its front and its darker side, a cornice, rows of framed windows, and a door with a step. */
      const building = (x, top, w, colour, { cols = 3, arched = false, frame = '#fff4d6', glass = '#8fd8de', door = true, windows = true } = {}) => {
        toned(`M${x + w} ${top}l9 6V${STREET}h-9Z`, colour, 0.28)
        flat(rect(x, top, w, STREET - top), colour)
        toned(rect(x - 3, top - 6, w + 6, 7), colour, 0.2)
        if (windows) {
          const gap = w / cols
          const ww = Math.min(16, gap - 10)
          let frames = ''
          let panes = ''
          let glints = ''
          for (let y = top + 16; y + 24 < STREET - (door ? 44 : 10); y += 32) {
            for (let c = 0; c < cols; c++) {
              const wx = x + gap * c + (gap - ww) / 2
              frames += rect(wx - 3, y - 3, ww + 6, 26)
              panes += arched ? `M${wx} ${y + 20}V${y + ww / 2}a${ww / 2} ${ww / 2} 0 0 1 ${ww} 0V${y + 20}Z` : rect(wx, y, ww, 20)
              glints += `M${wx + 3} ${y + 12}l6-7`
            }
          }
          flat(frames, frame)
          flat(panes, glass)
          line(glints, 'rgba(255,255,255,.6)', 1.6)
        }
        if (door) {
          const dx = x + w / 2 - 9
          flat(rect(dx - 3, STREET - 34, 24, 34), frame)
          flat(rect(dx, STREET - 31, 18, 31), '#9a5b3a')
          flat(circle(dx + 14, STREET - 15, 1.6), '#f2d27a')
          toned(rect(dx - 6, STREET - 4, 30, 4), '#d6dadb', 0.15)
        }
      }

      building(-280, 236, 130, '#e9a27b', { cols: 4 })
      building(-140, 196, 128, '#9fc5e8', { cols: 4, frame: '#eef7ff', glass: '#5d9bd1' })

      // The cheese house, a wedge with holes in it.
      toned('M110 200l9 6V390h-9Z', '#f6d65c', 0.28)
      flat('M4 390V226L110 200V390Z', '#f6d65c')
      for (const [cx, cy, r] of [[22, 246, 7], [52, 262, 10], [88, 236, 6], [92, 290, 9], [26, 310, 8], [66, 318, 5], [20, 362, 6], [96, 352, 7]]) flat(circle(cx, cy, r), '#e5b13c')
      flat('M48 390V368A10 10 0 0 1 68 368V390Z', '#c4813a')
      flat(circle(64, 236, 9), '#fff4d6')
      flat(circle(64, 236, 6.5), '#8fd8de')

      building(120, 168, 100, '#b9ad6c', { cols: 3 })
      toned(rect(132, 150, 12, 18), '#b9ad6c', 0.2)
      line('M128 200h6M200 232h6M150 280h6M190 300h6M130 330h6', '#a39859', 1.4)
      building(230, 236, 92, '#3fbcae', { arched: true, frame: '#c9f2ec', glass: '#2b9a90' })

      // The café: a low yellow front with a striped awning, its window and door, and a giant teacup on the roof.
      building(330, 330, 140, '#f6e07a', { windows: false, door: false })
      flat(rect(344, 350, 66, 34), '#e9573f')
      flat(rect(348, 354, 58, 30), '#cdeff2')
      line('M356 376l10-14M372 380l10-14', 'rgba(255,255,255,.7)', 1.6)
      flat(rect(420, 352, 26, 38), '#e9573f')
      flat(rect(424, 356, 18, 34), '#9a5b3a')
      let stripes = ''
      for (let x = 330, i = 0; x < 470; x += 14, i++) stripes += `M${x} 330h14v12a7 7 0 0 1-14 0z`
      flat(stripes, '#ffffff')
      let reds = ''
      for (let x = 330; x < 470; x += 28) reds += `M${x} 330h14v12a7 7 0 0 1-14 0z`
      flat(reds, '#e9573f')
      flat('M346 328a52 6 0 1 0 104 0a52 6 0 1 0-104 0Z', '#d9ab32')
      line('M436 288C460 286 460 314 432 314', '#ebc84f', 7)
      paint('M356 278H440C440 306 424 326 398 326S356 306 356 278Z', '#ebc84f', 4)
      flat('M356 278a42 6 0 1 0 84 0a42 6 0 1 0-84 0Z', '#f8e08a')
      flat('M362 278a36 4 0 1 0 72 0a36 4 0 1 0-72 0Z', '#c9952a')

      // The green block, a cactus growing up its wall.
      building(478, 248, 72, '#6dcb9c', { cols: 2, frame: '#e6fff2', glass: '#3f9e74' })
      line('M529 343H521C515 343 515 335 515 329V321M543 329H551C557 329 557 321 557 315V307', '#4fae5a', 8)
      paint('M529 390V302C529 292 543 292 543 302V390Z', '#4fae5a', 2)
      line('M532 312l-3-2M540 326l3-2M532 346l-3-2M540 362l3-2M532 378l-3-2', '#2f7d3a', 1.4)

      // The baseball house, with its seams, two framed windows a little askew, and a door.
      paint(circle(630, 332, 58), '#f8f5ee', 4)
      line('M588 292C604 316 604 348 588 372M672 292C656 316 656 348 672 372', '#e2867a', 3)
      line('M590 300l7-2M596 314l7-1M598 330h7M596 346l7 1M590 362l7 2M670 300l-7-2M664 314l-7-1M662 330h-7M664 346l-7 1M670 362l-7 2', '#e2867a', 2)
      for (const [wx, wy, turn] of [[612, 300, -8], [640, 330, 6]]) {
        const pane = element('g', { transform: `rotate(${turn} ${wx + 9} ${wy + 9})` }, parent)
        element('path', { d: rect(wx - 3, wy - 3, 24, 24), fill: '#f2d85a' }, pane)
        element('path', { d: rect(wx, wy, 18, 18), fill: '#9fd8f0' }, pane)
        stroke(`M${wx + 3} ${wy + 12}l6-7`, 'rgba(255,255,255,.7)', 1.6, pane)
      }
      flat('M620 390V372A10 10 0 0 1 640 372V390Z', '#d06d4f')

      // Behind the tree, a lilac tower with a dome, and plain blocks on past it.
      flat(circle(767, 196, 30), '#b9a5df')
      building(722, 196, 90, '#b9a5df', { cols: 3, frame: '#f3eeff', glass: '#8c7cc0' })
      building(822, 240, 120, '#f0a46b', { cols: 4 })
      building(952, 210, 110, '#8fc0e8', { cols: 3, frame: '#eef7ff', glass: '#5d9bd1' })

      // A little of the sky's haze over them, so they sit back behind the yard.
      flat(rect(-4000, 0, 8800, STREET), SKY).setAttribute('opacity', 0.22)
      // The street in front of them: the pavement in slabs, and the kerb.
      flat(rect(-4000, STREET, 8800, 28), '#d6dadb')
      let seams = ''
      for (let x = -400; x < 1200; x += 46) seams += `M${x} ${STREET}l-8 28`
      line(seams, '#c2c8cb', 1.4)
      flat(rect(-4000, STREET + 28, 8800, 4), '#9aa6ae')
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

    /** The bird on the lamp, who flies off when the wind gets up. */
    perch(parent) {
      const group = element('g', {}, element('g', { transform: 'translate(16 7)' }, parent))
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
          this.sunflower.wave()
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
          this.sunflower.hopping = Math.max(0, u * 1.25 - 0.25)
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
      this.sunflower.tick(time, dt, this.still)
      this.butterfly.tick(time, dt, this.wind, this.still)
      if (this.still) return
      // The world keeps moving gently: the clouds and the balloon drifting, the lamp glowing, the tree swaying.
      for (const { cloud, phase } of this.clouds) cloud.setAttribute('transform', `translate(${(Math.sin(time / 5200 + phase) * 14).toFixed(2)} 0)`)
      this.balloon.setAttribute('transform', `translate(${(Math.sin(time / 4100) * 24).toFixed(2)} ${(Math.sin(time / 1700) * 5).toFixed(2)})`)
      this.lantern.setAttribute('opacity', (0.85 + Math.sin(time / 260) * 0.15).toFixed(3))
      this.crown.setAttribute('transform', `rotate(${(Math.sin(time / 1300) * 0.8 + this.wind * 0.6).toFixed(3)} 702 260)`)
      ;[this.hanger, this.dilly, this.sunflower].forEach(({ hopping }, i) => {
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
