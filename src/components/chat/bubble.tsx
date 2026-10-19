import type { CSSProperties, ReactNode } from 'react'

import { cn } from '../../lib/utils'
import type { ChatMessage } from '../../types'

const EMAILS = /([^\s@]+@[^\s@]+\.[^\s@.,!?]{2,})/

/** A line of text with each email address in it linked, as Messages links them. */
const Linked = ({ text }: { text: string }) => {
  return text.split(EMAILS).map((part, i) =>
    i % 2 ? (
      <a key={i} href={`mailto:${part}`} className="underline underline-offset-2">
        {part}
      </a>
    ) : (
      part
    ),
  )
}

/** The page of a PDF as Messages draws a document: white, its corner folded, the format on a red band. */
const PdfIcon = () => {
  return (
    <svg viewBox="0 0 34 42" aria-hidden="true" className="h-[42px] w-[34px] shrink-0 drop-shadow-[0_0.5px_1px_rgb(0_0_0/0.25)]">
      <path d="M3 0h20l11 11v28a3 3 0 0 1-3 3H3a3 3 0 0 1-3-3V3a3 3 0 0 1 3-3Z" fill="#fff" />
      <path d="M23 0v8a3 3 0 0 0 3 3h8Z" fill="#d6d6db" />
      <rect x="0" y="25" width="34" height="11" fill="#e5332a" />
      <text x="17" y="33.6" textAnchor="middle" fontSize="8.5" fontWeight="700" fill="#fff" fontFamily="system-ui, -apple-system, sans-serif">
        PDF
      </text>
    </svg>
  )
}

/**
 * One message in the thread, on its sender's side: grey for me, blue for the reader. The last of a run from the same
 * sender has a tail. A photograph has none, as in Messages. order staggers the opening thread's arrival.
 */
export const Bubble = ({ message, tail, order, children }: { message: ChatMessage; tail: boolean; order?: number; children?: ReactNode }) => {
  const mine = message.side === 'me'
  const tone = mine ? 'chat-in' : 'chat-out'
  const shape = cn('chat-bubble', tone, tail && 'chat-tail')
  const style = { '--order': order ?? 0 } as CSSProperties

  let body: ReactNode
  if (message.kind === 'photo') {
    body = (
      <img
        src={message.src}
        alt={message.alt}
        width={message.size[0]}
        height={message.size[1]}
        className="block h-auto w-[min(56vw,13.5rem)] rounded-[18px] bg-[var(--chat-in)]"
      />
    )
  } else if (message.kind === 'link') {
    body = (
      <a
        href={message.href}
        target="_blank"
        rel="noopener"
        className={cn(shape, 'flex w-[min(68vw,17rem)] items-center gap-3 py-2.5 pr-2.5 pl-3.5 outline-offset-2 focus-visible:outline-2 focus-visible:outline-[var(--chat-blue)]')}
      >
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[15px] leading-5 font-semibold">{message.title}</span>
          <span className="block truncate text-[13px] leading-[18px] text-[var(--chat-quiet)]">{new URL(message.href).host}</span>
        </span>
        <img src={message.icon} alt="" width={44} height={44} className="size-11 shrink-0 rounded-[10px] bg-white" />
      </a>
    )
  } else if (message.kind === 'file') {
    body = (
      <a
        href={message.href}
        target="_blank"
        rel="noopener"
        className={cn(shape, 'flex w-[min(70vw,17.5rem)] items-center gap-3 py-2.5 pr-4 pl-3 outline-offset-2 focus-visible:outline-2 focus-visible:outline-[var(--chat-blue)]')}
      >
        <PdfIcon />
        <span className="min-w-0">
          <span className="block truncate text-[15px] leading-5 font-semibold">{message.name}</span>
          <span className="block truncate text-[13px] leading-[18px] text-[var(--chat-quiet)]">{message.detail}</span>
        </span>
      </a>
    )
  } else {
    body = (
      <p className={cn(shape, 'px-3 py-[7px] text-[17px] leading-[22px] tracking-[-0.01em] [overflow-wrap:anywhere] whitespace-pre-wrap')}>
        <Linked text={message.text} />
      </p>
    )
  }

  return (
    <div data-side={message.side} style={style} className={cn('chat-arrive flex flex-col', mine ? 'items-start' : 'items-end')}>
      <div className={cn('max-w-[min(78%,27rem)]', mine ? 'ml-2' : 'mr-2')}>
        <span className="sr-only">{mine ? 'Anurag: ' : 'You: '}</span>
        {body}
      </div>
      {children}
    </div>
  )
}
