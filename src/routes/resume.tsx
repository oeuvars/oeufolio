import { createFileRoute } from '@tanstack/react-router'

import { ResumeLetter } from '../components/resume-letter'
import letterCss from '../components/resume-letter.css?url'
import { pages } from '../content'
import { seo } from '../lib/seo'

/** The résumé as a typed letter, outside the stack of folders. */
export const Route = createFileRoute('/resume')({
  staticData: { bare: true },
  head: () => {
    const head = seo(pages.resume)
    return { ...head, links: [...head.links, { rel: 'stylesheet', href: letterCss }] }
  },
  component: ResumeLetter,
})
