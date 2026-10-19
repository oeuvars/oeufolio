import { useRef, useState, type KeyboardEvent } from 'react'

import { profile } from '../../content'
import { cn } from '../../lib/utils'

/** A Gmail draft to me, in a new tab, with the reader's message as its body. */
const gmail = (subject: string, body: string) => {
  const query = new URLSearchParams({ view: 'cm', fs: '1', to: profile.email, su: subject, body })
  return `https://mail.google.com/mail/?${query}`
}

/**
 * Messages' compose field, pinned to the foot of the page: a pill that grows with what is typed and a blue send
 * arrow. The arrow is a link that opens what was typed as a Gmail draft to me. Return follows it too, and
 * Shift-Return starts a new line.
 */
export const Composer = ({ placeholder, subject, onSend }: { placeholder: string; subject: string; onSend: (text: string) => void }) => {
  const [text, setText] = useState('')
  const field = useRef<HTMLTextAreaElement>(null)
  const link = useRef<HTMLAnchorElement>(null)
  const ready = text.trim().length > 0

  const fit = () => {
    const area = field.current
    if (!area) return
    area.style.height = 'auto'
    area.style.height = `${Math.min(area.scrollHeight, 132)}px`
  }

  // The link has opened the draft by the time this runs; the thread keeps a copy of what was sent.
  const sent = () => {
    onSend(text.trim())
    setText('')
    requestAnimationFrame(fit)
  }

  const key = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== 'Enter' || event.shiftKey || event.nativeEvent.isComposing) return
    event.preventDefault()
    if (ready) link.current?.click()
  }

  return (
    <footer className="shrink-0 border-t border-[var(--chat-rule)] bg-[var(--chat-bar)]">
      <div className="mx-auto flex max-w-[44rem] items-end px-3 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        <div className="flex min-h-9 flex-1 items-end rounded-[19px] border border-[var(--chat-rule)] bg-[var(--chat-field)] py-[3px] pr-[3px] pl-3.5">
          <textarea
            ref={field}
            rows={1}
            value={text}
            aria-label="Message Anurag"
            placeholder={placeholder}
            onChange={(event) => {
              setText(event.target.value)
              fit()
            }}
            onKeyDown={key}
            enterKeyHint="send"
            className="block max-h-[132px] min-h-7 flex-1 resize-none bg-transparent py-[3px] text-[17px] leading-[22px] tracking-[-0.01em] text-[var(--chat-ink)] outline-none placeholder:text-[var(--chat-quiet)]"
          />
          <a
            ref={link}
            href={ready ? gmail(subject, text.trim()) : undefined}
            target="_blank"
            rel="noopener"
            onClick={ready ? sent : undefined}
            aria-label="Send in Gmail"
            aria-disabled={!ready}
            className={cn(
              'ml-2 grid size-7 shrink-0 place-items-center rounded-full text-white transition-[opacity,transform] duration-200 active:scale-90',
              'bg-[var(--chat-blue)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--chat-blue)]',
              ready ? 'opacity-100' : 'pointer-events-none scale-75 opacity-0',
            )}
          >
            <svg viewBox="0 0 16 16" aria-hidden="true" className="size-4">
              <path d="M8 13V3.5M3.5 7.5 8 3l4.5 4.5" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        </div>
      </div>
    </footer>
  )
}
