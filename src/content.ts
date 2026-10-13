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
    alt: "A handwritten letter on a cream card, dated Oct 2026, too late. Hello younger me, I must admit I was quite excited to send a letter to you! Hopefully this survives its backwards journey (let alone the years in between). I also must admit that you will find all of it stupid for quite some time yet, so that probably explains the excitement. And I play an electric guitar now, which is loud, preferably. I wet shave too. It's actually stupid how long I take with a Merkur razor, Proraso and Clubman aftershave. Simply put, I am a bore. Hopefully I make sense someday. Apart from that, I've been trying to watch Arsenal win and shout up the Gunners in general. Especially since the cats became chief supervisors... are there any movies or music you've been particularly enjoying? I'd love to know! I've been occupied with loud guitars and slow mornings. Quite the combination... Cheers, Anurag. Drawn in the margins: an envelope melting, with the question, can a letter age? Someone at a laptop: one of my favorite videos to put on is a full Arsenal match. Up the Gunners. Someone in bed with a hand over their face: I lose sleep over it. A lecturer holding something up to a class: why feel the need to use foam when this soap exists? The class: who let you in here. Who are you. And someone face down on the floor: I can't believe this is who I grow up to be... life is so unfair!",
  },
  experience: [
    {
      period: '2024 to now',
      role: 'Software Engineer',
      org: 'Company One',
      summary: 'One or two lines on what you owned and what changed because of it.',
    },
    {
      period: '2022 to 2024',
      role: 'Software Engineer',
      org: 'Company Two',
      summary: 'One or two lines on what you owned and what changed because of it.',
    },
    {
      period: '2020 to 2022',
      role: 'Junior Engineer',
      org: 'Company Three',
      summary: 'One or two lines on what you owned and what changed because of it.',
    },
  ],
  works: [
    {
      title: 'Project One',
      summary: 'One line on what it does and why it exists.',
      category: 'Tool',
      year: '2026',
      href: 'https://github.com/oeuvars',
    },
    {
      title: 'Project Two',
      summary: 'One line on what it does and why it exists.',
      category: 'Service',
      year: '2025',
      href: 'https://github.com/oeuvars',
    },
    {
      title: 'Project Three',
      summary: 'One line on what it does and why it exists.',
      category: 'Experiment',
      year: '2024',
      href: 'https://github.com/oeuvars',
    },
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
