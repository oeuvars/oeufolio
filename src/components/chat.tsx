import { Link } from '@tanstack/react-router'
import { useEffect, useRef, useState } from 'react'

import { chat } from '../content'
import type { ChatMessage } from '../types'
import { Bubble } from './chat/bubble'
import { Composer } from './chat/composer'
import { Typing } from './chat/typing'

/** A message the reader or I added after the page opened. */
type Live = ChatMessage & { id: number }

/** How long I seem to type a reply: longer for a longer one, never long enough to wait on. */
const typingTime = (text: string) => Math.min(600 + text.length * 14, 1500)

/** Whether a message ends its sender's run, so it takes the tail. */
const ends = (thread: ChatMessage[], i: number) => thread[i + 1]?.side !== thread[i].side

/** "9:41 AM", the time the reader opened the page, which is when Messages would say the thread came in. */
const useOpenedAt = () => {
  const [time, setTime] = useState('')
  useEffect(() => setTime(new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })), [])
  return time
}

/**
 * The résumé as an iMessage thread with me. The reader's side asks what a résumé answers and mine replies, with a
 * photograph, link previews and the PDF as an attachment. Below it the reader can text me: sending opens the message
 * as a Gmail draft to me, and the thread keeps a copy with my reply.
 */
export const Conversation = () => {
  const [live, setLive] = useState<Live[]>([])
  const [typing, setTyping] = useState(false)
  const nextId = useRef(0)
  const scroller = useRef<HTMLElement>(null)
  const opened = useOpenedAt()

  const thread: ChatMessage[] = [...chat.thread, ...live]
  // Messages says Read under the reader's last message. Theirs from the composer went to Gmail, so it says nothing.
  const read = chat.thread.map((message) => message.side).lastIndexOf('you')

  // The page itself never scrolls, only the thread, so the thread takes focus at once and the scroll keys move it.
  useEffect(() => scroller.current?.focus({ preventScroll: true }), [])

  // Each new message, and my typing, scrolls the thread to its foot.
  useEffect(() => {
    if (live.length === 0 && !typing) return
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: 'smooth' })
  }, [live.length, typing])

  const add = (side: ChatMessage['side'], text: string) => setLive((all) => [...all, { id: nextId.current++, side, kind: 'text', text }])

  const send = (text: string) => {
    add('you', text)
    setTyping(true)
    window.setTimeout(() => {
      setTyping(false)
      add('me', chat.reply)
    }, typingTime(chat.reply))
  }

  return (
    <div className="imessage flex h-dvh flex-col overflow-hidden antialiased">
      <h1 className="sr-only">Anurag Das, résumé</h1>

      <header className="shrink-0 border-b border-[var(--chat-rule)] bg-[var(--chat-bar)]">
        <div className="mx-auto grid max-w-[44rem] grid-cols-[1fr_auto_1fr] items-center px-2 pt-[max(0.5rem,env(safe-area-inset-top))] pb-1.5">
          <Link
            to="/"
            aria-label="Back to the site"
            className="flex size-10 items-center justify-center justify-self-start rounded-full text-[var(--chat-blue)] focus-visible:outline-2 focus-visible:outline-[var(--chat-blue)]"
          >
            <svg viewBox="0 0 12 20" aria-hidden="true" className="h-5 w-3">
              <path d="M10 2 2 10l8 8" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
          <div className="flex flex-col items-center">
            <img src={chat.contact.avatar} alt="" width={44} height={44} className="size-11 rounded-full bg-[var(--chat-in)] object-cover" />
            <p className="mt-1 flex items-center gap-0.5 text-[12px] leading-4 font-medium">
              {chat.contact.name}
              <svg viewBox="0 0 6 10" aria-hidden="true" className="h-2 w-1.5 text-[var(--chat-quiet)]">
                <path d="m1 1 4 4-4 4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </p>
          </div>
        </div>
      </header>

      <main
        ref={scroller}
        tabIndex={-1}
        className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto overscroll-contain outline-none [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        <div className="mx-auto max-w-[44rem] px-3 pt-4 pb-6">
          <p className="mb-3 text-center text-[11px] leading-[14px] text-[var(--chat-quiet)]">
            <span className="font-semibold">iMessage</span>
            <br />
            Today{opened && ` ${opened}`}
          </p>

          <div role="log" aria-label="Conversation with Anurag" aria-live="polite">
            {thread.map((message, i) => {
              const receipt = i === read && live.length === 0
              return (
                <div key={'id' in message ? `live-${message.id}` : i} className={i > 0 && thread[i - 1].side !== message.side ? 'mt-3.5' : 'mt-0.5'}>
                  <Bubble message={message} tail={ends(thread, i)} order={i < chat.thread.length ? Math.min(i, 14) : 0}>
                    {receipt && (
                      <p className="mt-0.5 mr-2 text-[11px] leading-[14px] font-semibold text-[var(--chat-quiet)]">Read</p>
                    )}
                  </Bubble>
                </div>
              )
            })}
            {typing && <Typing />}
          </div>
        </div>
      </main>

      <Composer placeholder={chat.placeholder} subject={chat.subject} onSend={send} />
    </div>
  )
}
