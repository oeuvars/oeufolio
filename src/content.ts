import type { Profile } from './types'

export const profile: Profile = {
  handle: 'oeuvars',
  nav: [
    { to: '/', label: 'Basics' },
    { to: '/likes', label: 'Likes' },
    { to: '/work', label: 'Work' },
    { to: '/extras', label: 'Extras' },
  ],
  badge: {
    src: '/objects/badge.avif',
    backdrop: { color: '#e3d3c1' },
    alt: 'An ID card in a clear vinyl holder on a steel ring. It reads The Performer, Drop 25, product-first engineer, Cybership. Name: Anurag Das. Occupation: Engineer. Shade: T3 Warm. The holder of this card is an official performer for me. 02-03X.',
  },
  letter: {
    src: '/objects/letter.avif',
    alt: "A handwritten letter, dated Oct 2026, too late. Hello younger me, I know what you're like, so I know you'll call all of this stupid. I'm telling you anyway. You pick up an electric guitar and you don't put it down. You learn to shave slowly, the old way, and it ends up being the part of the morning that is yours. You give your heart to Arsenal, which is a stupid thing to do with a heart. And the cats. You think you are not a cat person. Then one falls asleep next to you, belly up, trusting you completely, and that is that. It isn't impressive, any of it, and I wouldn't trade it. Take your time getting here. Cheers, Anurag. Drawn between the lines: an amplifier and a PRS Silver Sky, noted loud, preferably. A lathered face in a mirror saying stretch and go with the grain, beside a shelf holding a Merkur razor, a tub of Proraso and a bottle of Clubman, while a younger onlooker says how relaxing! Someone holding a scarf up at a football match on television, shouting Özil, and the onlooker saying golly! A cat asleep on its back on a cushion, belly up, paws in the air. And me on a bench, pressing 225 lbs: damn, light work.",
  },
  experience: [
    { period: 'Mar 2025 to now', org: 'Cybership', room: 'warehouse' },
    { period: 'Jul 2024 to Mar 2025', org: 'Ekarth Ventures', room: 'bank' },
    { period: 'Aug 2023 to Jul 2024', org: 'ProperSKU', room: 'dock' },
  ],
  extras: {
    plates: [
      { title: 'Untitled I', caption: 'Medium, year.' },
      { title: 'Untitled II', caption: 'Medium, year.' },
      { title: 'Untitled III', caption: 'Medium, year.' },
      { title: 'Untitled IV', caption: 'Medium, year.' },
    ],
    playlist: {
      title: 'On repeat',
      note: 'What is playing while I work.',
      href: 'https://open.spotify.com',
    },
  },
  socials: [
    { label: 'GitHub', href: 'https://github.com/oeuvars' },
    { label: 'X', href: 'https://x.com/oeuvars' },
    { label: 'LinkedIn', href: 'https://linkedin.com/in/oeuvars' },
  ],
  email: 'sudo@anurag.gg',
}
