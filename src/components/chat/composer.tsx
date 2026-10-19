import { useRef, useState, type FormEvent, type KeyboardEvent } from 'react'

import { cn } from '../../lib/utils'

/**
 * Messages' compose field, pinned to the foot of the page: a pill that grows with what is typed and a blue send
 * arrow. Return sends and Shift-Return starts a new line. When I have asked for an email it takes one, and website
 * is a field only a bot would see and fill in.
 */
export const Composer = ({ placeholder, email, busy, onSend }: { placeholder: string; email: boolean; busy: boolean; onSend: (text: string, website: string) => void }) => {
  const [text, setText] = useState('')
  const field = useRef<HTMLTextAreaElement>(null)
  const trap = useRef<HTMLInputElement>(null)
  const ready = text.trim().length > 0 && !busy

  const fit = () => {
    const area = field.current
    if (!area) return
    area.style.height = 'auto'
    area.style.height = `${Math.min(area.scrollHeight, 132)}px`
  }

  const send = (event?: FormEvent) => {
    event?.preventDefault()
    if (!ready) return
    onSend(text.trim(), trap.current?.value ?? '')
    setText('')
    requestAnimationFrame(fit)
  }

  const key = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) send(event)
  }

  return (
    <footer className="sticky bottom-0 z-10 border-t border-[var(--chat-rule)] bg-[var(--chat-bar)] backdrop-blur-xl backdrop-saturate-150">
      <form onSubmit={send} className="mx-auto flex max-w-[44rem] items-end gap-2 px-3 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        <input ref={trap} name="website" tabIndex={-1} autoComplete="off" aria-hidden="true" className="absolute -left-[9999px] size-px opacity-0" />
        <label className="flex min-h-9 flex-1 items-end rounded-[19px] border border-[var(--chat-rule)] bg-[var(--chat-field)] py-[3px] pr-[3px] pl-3.5">
          <span className="sr-only">{email ? 'Your email' : 'Message Anurag'}</span>
          <textarea
            ref={field}
            rows={1}
            value={text}
            placeholder={placeholder}
            onChange={(event) => {
              setText(event.target.value)
              fit()
            }}
            onKeyDown={key}
            inputMode={email ? 'email' : 'text'}
            autoComplete={email ? 'email' : 'off'}
            autoCapitalize={email ? 'off' : 'sentences'}
            spellCheck={!email}
            enterKeyHint="send"
            maxLength={4000}
            className="block max-h-[132px] min-h-7 flex-1 resize-none bg-transparent py-[3px] text-[17px] leading-[22px] tracking-[-0.01em] text-[var(--chat-ink)] outline-none placeholder:text-[var(--chat-quiet)]"
          />
          <button
            type="submit"
            disabled={!ready}
            aria-label="Send"
            className={cn(
              'ml-2 grid size-7 shrink-0 place-items-center rounded-full text-white transition-[opacity,transform] duration-200 active:scale-90',
              'bg-[var(--chat-blue)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--chat-blue)]',
              ready ? 'opacity-100' : 'opacity-0 scale-75',
            )}
          >
            <svg viewBox="0 0 16 16" aria-hidden="true" className="size-4">
              <path d="M8 13V3.5M3.5 7.5 8 3l4.5 4.5" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </label>
      </form>
    </footer>
  )
}
