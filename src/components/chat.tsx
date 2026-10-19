import { Link } from '@tanstack/react-router'
import { useEffect, useRef, useState } from 'react'

import { chat, profile } from '../content'
import { isEmail } from '../lib/utils'
import { sendNote } from '../server/send-note'
import type { ChatMessage } from '../types'
import { Bubble } from './chat/bubble'
import { Composer } from './chat/composer'
import { Typing } from './chat/typing'

/** A message the reader or I added after the page opened, and for the reader's, whether it reached my inbox. */
type Live = ChatMessage & { id: number; receipt?: 'sending' | 'delivered' | 'failed' }

/** Where the composer is: waiting for a note, waiting for the reader's email to go with it, or able to send. */
type Stage = 'message' | 'email' | 'ready'

const RECEIPT = { sending: 'Sending…', delivered: 'Delivered', failed: 'Not Delivered' }

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
 * photograph, link previews and the PDF as an attachment. Below it the reader can text me: I ask for an email to
 * write back to, and the note goes to my inbox through the server (src/server/send-note.ts).
 */
export const Conversation = () => {
  const [live, setLive] = useState<Live[]>([])
  const [stage, setStage] = useState<Stage>('message')
  const [typing, setTyping] = useState(false)
  const [sending, setSending] = useState(false)
  const pending = useRef('')
  const email = useRef('')
  const nextId = useRef(0)
  const opened = useOpenedAt()

  const thread: ChatMessage[] = [...chat.thread, ...live]
  const lastYours = thread.map((message) => message.side).lastIndexOf('you')

  // Each new message, and my typing, scrolls the thread to its foot.
  useEffect(() => {
    if (live.length === 0 && !typing) return
    window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' })
  }, [live.length, typing])

  const add = (side: ChatMessage['side'], text: string, receipt?: Live['receipt']) => {
    const id = nextId.current++
    setLive((all) => [...all, { id, side, kind: 'text', text, receipt }])
    return id
  }

  const mark = (id: number, receipt: Live['receipt']) => setLive((all) => all.map((message) => (message.id === id ? { ...message, receipt } : message)))

  const reply = (text: string) => {
    setTyping(true)
    window.setTimeout(() => {
      setTyping(false)
      add('me', text)
    }, typingTime(text))
  }

  const deliver = async (id: number, message: string, website: string) => {
    setSending(true)
    const receipt = await sendNote({ data: { message, email: email.current, website } }).catch(() => ({ ok: false as const }))
    setSending(false)
    mark(id, receipt.ok ? 'delivered' : 'failed')
    setStage('ready')
    if (!receipt.ok) return reply(chat.replies.failed.replace('{address}', profile.email))
    reply(stage === 'ready' ? chat.replies.more : chat.replies.sent.replace('{email}', email.current))
  }

  const send = (text: string, website: string) => {
    if (stage === 'message') {
      add('you', text)
      pending.current = text
      setStage('email')
      return reply(chat.replies.askEmail)
    }
    if (stage === 'email') {
      if (!isEmail(text)) {
        add('you', text)
        return reply(chat.replies.badEmail)
      }
      email.current = text
      return deliver(add('you', text, 'sending'), pending.current, website)
    }
    deliver(add('you', text, 'sending'), text, website)
  }

  return (
    <div className="imessage min-h-dvh antialiased">
      <h1 className="sr-only">Anurag Das, résumé</h1>

      <header className="sticky top-0 z-10 border-b border-[var(--chat-rule)] bg-[var(--chat-bar)] backdrop-blur-xl backdrop-saturate-150">
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

      <main className="mx-auto max-w-[44rem] px-3 pt-4 pb-6">
        <p className="mb-3 text-center text-[11px] leading-[14px] text-[var(--chat-quiet)]">
          <span className="font-semibold">iMessage</span>
          <br />
          Today{opened && ` ${opened}`}
        </p>

        <div role="log" aria-label="Conversation with Anurag" aria-live="polite">
          {thread.map((message, i) => {
            const receipt = i === lastYours ? ((message as Live).receipt ?? 'read') : undefined
            return (
              <div key={'id' in message ? `live-${message.id}` : i} className={i > 0 && thread[i - 1].side !== message.side ? 'mt-3.5' : 'mt-0.5'}>
                <Bubble message={message} tail={ends(thread, i)} order={i < chat.thread.length ? Math.min(i, 14) : 0}>
                  {receipt && (
                    <p className={`mt-0.5 mr-2 text-[11px] leading-[14px] ${receipt === 'failed' ? 'text-[#ff3b30]' : 'text-[var(--chat-quiet)]'}`}>
                      {receipt === 'read' ? <span className="font-semibold">Read</span> : RECEIPT[receipt]}
                    </p>
                  )}
                </Bubble>
              </div>
            )
          })}
          {typing && <Typing />}
        </div>
      </main>

      <Composer placeholder={stage === 'email' ? chat.placeholder.email : chat.placeholder.message} email={stage === 'email'} busy={sending} onSend={send} />
    </div>
  )
}
