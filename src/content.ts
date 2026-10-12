import type { Profile } from './types'

export const profile: Profile = {
  handle: 'oeuvars',
  role: 'Software engineer',
  headline: { before: 'Good software should feel ', accent: 'obvious', after: '.' },
  intro: [
    'I build products end to end, from the first sketch to the production deploy, and I obsess over details most people will not consciously notice. But they will feel them.',
    'I am a generalist, and I have a passion for coherence.',
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
  now: 'Developing skill through doing, guiltlessly exploring passion and interests, imbuing quality. Mindful that everything around me is someone\'s life work.',
  questions: [
    { q: 'How do I reach you?', a: 'Fastest way is to email me. Keep it short, do not write me an essay.' },
    { q: 'Are you available?', a: 'Sometimes. Ask.' },
    { q: 'Will you read a long pitch?', a: 'No.' },
  ],
  socials: [
    { label: 'GitHub', href: 'https://github.com/oeuvars' },
    { label: 'X', href: 'https://x.com/oeuvars' },
    { label: 'LinkedIn', href: 'https://linkedin.com/in/oeuvars' },
  ],
  email: 'sudo@anurag.gg',
  colophon:
    'Set in EB Garamond and IM Fell English. Parchment rendered in Blender. Built with TanStack Start.',
}
