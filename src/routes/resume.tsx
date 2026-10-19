import { createFileRoute } from '@tanstack/react-router'

import { Conversation } from '../components/chat'
import chatCss from '../components/chat.css?url'
import { pages } from '../content'
import { seo } from '../lib/seo'

/** The résumé as a text thread with me, outside the stack of folders. */
export const Route = createFileRoute('/resume')({
  staticData: { bare: true },
  head: () => {
    const head = seo(pages.resume)
    return { ...head, links: [...head.links, { rel: 'stylesheet', href: chatCss }] }
  },
  component: Conversation,
})
