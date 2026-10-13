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
    alt: 'An ID card in a clear vinyl holder on a steel ring. It reads The Performer, Drop 25. Name: Anurag Das. Occupation: Engineer. Shade: T3 Warm.',
  },
  likes: [
    {
      title: 'Electric guitar',
      tag: 'Strings',
      note: 'Loud, preferably.',
    },
    {
      title: 'Wet shaving',
      tag: 'Ritual',
      note: 'A slow morning ritual, done properly.',
      details: ['Merkur razor', 'Proraso', 'Clubman aftershave'],
    },
    {
      title: 'Arsenal',
      tag: 'Football',
      note: 'Up the Gunners.',
    },
    {
      title: 'Cats',
      tag: 'Company',
      note: 'Chief supervisors of everything I build.',
    },
  ],
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
