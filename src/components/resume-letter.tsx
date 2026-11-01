import '@fontsource/courier-prime/400.css'
import '@fontsource/courier-prime/700.css'

import { Link } from '@tanstack/react-router'
import { useState, type CSSProperties } from 'react'

import { resumeLetter } from '../content'

const DATE = { month: 'long', day: 'numeric', year: 'numeric' } as const

const MARKS = /(==.+?==|!!.+?!!|~~.+?~~)/
const EMAILS = /([^\s@]+@[^\s@]+\.[^\s@.,!?]{2,})/

/** A run of typed text with each email address in it linked. */
const Linked = ({ text }: { text: string }) => {
  return text.split(EMAILS).map((part, i) =>
    i % 2 ? (
      <a key={i} href={`mailto:${part}`} className="typed-link">
        {part}
      </a>
    ) : (
      part
    ),
  )
}

/**
 * The résumé as a letter off a typewriter, after Wolfgang Weingart's 1986 letter to AIGA/Boston: my address and the
 * reader's, the day it is read, the letter itself with what matters marked over in highlighter and a few second
 * thoughts struck out in x's, my signature in pen, and what comes with it typed underneath.
 */
export const ResumeLetter = () => {
  const { sender, place, recipient, salutation, body, closing, signature, enclosures } = resumeLetter
  // The reader's name, typed or autofilled into the blank under To. No browser API gives a page the visitor's name
  // unasked; autocomplete="name" is the nearest, offering the name the browser has saved for them in one tap.
  const [name, setName] = useState('')
  const reader = name.trim()
  // Each mark is swept on in turn down the page, as if drawn after the letter was typed.
  let mark = 0

  const typed = (text: string) =>
    text.split(MARKS).map((part, j) => {
      if (j % 2 === 0) return <Linked key={j} text={part} />
      const inner = part.slice(2, -2)
      // Struck out the way a typist did it: backspaced and overtyped with an x on every character.
      if (part.startsWith('~~'))
        return (
          <del key={j} className="typed-strike" data-x={'x'.repeat(inner.length)}>
            {inner}
          </del>
        )
      return (
        <mark key={j} className={part.startsWith('!!') ? 'typed-mark typed-mark-red' : 'typed-mark'} style={{ '--mark': mark++ } as CSSProperties}>
          <Linked text={inner} />
        </mark>
      )
    })

  return (
    <div className="typed-letter min-h-dvh px-0 py-0 sm:px-6 sm:py-10">
      <Link to="/" className="typed-link mx-auto mb-4 hidden max-w-[52rem] text-[13px] text-[#6b6b6b] sm:block">
        &larr; anurag.gg
      </Link>

      {/* Typewriter ink: letters worn ragged at the edges, struck darker or lighter one to the next, and bled a little
          into the paper. */}
      <svg aria-hidden="true" className="absolute size-0">
        <filter id="typed-ink" x="-2%" y="-2%" width="104%" height="104%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4" result="grit" />
          <feDisplacementMap in="SourceGraphic" in2="grit" scale="0.6" xChannelSelector="R" yChannelSelector="G" result="worn" />
          <feGaussianBlur in="worn" stdDeviation="0.2" result="soft" />
          <feComponentTransfer in="soft" result="bled">
            <feFuncA type="linear" slope="1.6" intercept="0" />
          </feComponentTransfer>
          <feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="2" seed="11" result="strike" />
          <feColorMatrix in="strike" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.9 0 0 0 0.5" result="density" />
          <feComposite in="bled" in2="density" operator="in" />
        </filter>
        {/* Pen ink on the same paper: the stroke's edge a little ragged, and the paper's tooth showing through where the
            pen ran dry. */}
        <filter id="pen-ink" x="-2%" y="-2%" width="104%" height="104%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7" result="grit" />
          <feDisplacementMap in="SourceGraphic" in2="grit" scale="1.2" xChannelSelector="R" yChannelSelector="G" result="worn" />
          <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="3" seed="23" result="tooth" />
          <feColorMatrix in="tooth" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.5 0 0 0 0.12" result="density" />
          <feComposite in="worn" in2="density" operator="in" />
        </filter>
      </svg>

      <article className="typed-sheet mx-auto max-w-[52rem] bg-[#fdfdfb] px-6 pt-8 pb-16 text-[13px] leading-[1.22] shadow-[0_1px_2px_rgb(0_0_0/0.08),0_8px_30px_rgb(0_0_0/0.06)] sm:px-[clamp(2.5rem,9vw,7rem)] sm:pt-16 sm:pb-24 sm:text-[15px]">
        <div className="typed-ink">
        <h1 className="sr-only">Anurag Das, résumé</h1>
        <Link to="/" className="typed-link mb-6 inline-block text-[#6b6b6b] sm:hidden">
          &larr; anurag.gg
        </Link>

        <address className="not-italic">
          {sender.map((line, i) => (
            <span key={line} className={i === sender.length - 1 ? 'block underline decoration-1 underline-offset-[3px]' : 'block'}>
              {i === 0 ? (
                <mark className="typed-mark" style={{ '--mark': mark++ } as CSSProperties}>
                  {line}
                </mark>
              ) : (
                line
              )}
            </span>
          ))}
        </address>

        <div className="mt-14 grid gap-10 sm:mt-24 sm:grid-cols-[1fr_1fr] sm:gap-6">
          <p>
            {place},
            <br />
            {/* The day on the reader's own calendar, from the first paint. The server renders in UTC, a day out for
                half the world at some hour, so the script under it puts in the browser's date as the page is read,
                and React keeps that text when it hydrates. A page opened by client navigation renders it there. */}
            <span id="letter-date" suppressHydrationWarning>
              {new Date().toLocaleDateString('en-US', DATE)}
            </span>
            <script
              dangerouslySetInnerHTML={{
                __html: `document.getElementById('letter-date').textContent=new Date().toLocaleDateString('en-US',${JSON.stringify(DATE)})`,
              }}
            />
          </p>
          <div>
            <p className="mb-[1.22em]">To</p>
            <input
              type="text"
              name="name"
              autoComplete="name"
              aria-label="Your name"
              placeholder={recipient.blank}
              maxLength={40}
              value={name}
              onChange={(event) => setName(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
              className="typed-blank block w-full max-w-[26ch]"
            />
            <p>{recipient.address}</p>
          </div>
        </div>

        <div className="mt-14 max-w-[64ch] sm:mt-24">
          <p>{reader ? `${salutation.greeting} ${reader},` : typed(salutation.anonymous)}</p>
          {body.map((paragraph, i) => (
            <p key={i} className={i === 0 ? '' : 'mt-[1.22em]'}>
              {typed(paragraph)}
            </p>
          ))}

          <p className="mt-[1.22em]">{typed(closing)}</p>
        </div>
        </div>

        {/* Signed in pen, so in pen's ink and not the typewriter's. */}
        <img
          src={signature.src}
          alt={signature.alt}
          width={signature.size[0]}
          height={signature.size[1]}
          className="typed-pen mt-3 ml-1 block h-auto w-[13em] -rotate-2 sm:ml-4"
        />

        <div className="typed-ink">
          <dl className="mt-10 grid grid-cols-[auto_1fr] gap-x-[1ch] sm:mt-16">
            <dt>Encl.</dt>
            <dd>
              {enclosures.map((item) => (
                <a key={item.href} href={item.href} target="_blank" rel="noopener" className="typed-link block w-fit">
                  {item.label}
                </a>
              ))}
            </dd>
          </dl>
        </div>
      </article>
    </div>
  )
}
