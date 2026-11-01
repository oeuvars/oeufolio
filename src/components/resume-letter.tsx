import '@fontsource/courier-prime/400.css'
import '@fontsource/courier-prime/700.css'
import '@fontsource/nothing-you-could-do/400.css'

import { Link } from '@tanstack/react-router'
import type { CSSProperties } from 'react'

import { resumeLetter } from '../content'

const MARKS = /(==.+?==|!!.+?!!)/
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
 * reader's, the day it is read, the letter itself with what matters marked over in highlighter, a signature in pen,
 * and what comes with it typed underneath.
 */
export const ResumeLetter = () => {
  const { sender, place, recipient, salutation, body, closing, signature, enclosures } = resumeLetter
  const country = recipient.at(-1) ?? ''
  // Each mark is swept on in turn down the page, as if drawn after the letter was typed.
  let mark = 0

  return (
    <div className="typed-letter min-h-dvh px-0 py-0 sm:px-6 sm:py-10">
      <Link to="/" className="typed-link mx-auto mb-4 hidden max-w-[52rem] text-[13px] text-[#6b6b6b] sm:block">
        &larr; anurag.gg
      </Link>

      <article className="mx-auto max-w-[52rem] bg-white px-6 pt-8 pb-16 text-[13px] leading-[1.22] shadow-[0_1px_2px_rgb(0_0_0/0.08),0_8px_30px_rgb(0_0_0/0.06)] sm:px-[clamp(2.5rem,9vw,7rem)] sm:pt-16 sm:pb-24 sm:text-[15px]">
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
            <span suppressHydrationWarning>{new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
          </p>
          <p>
            {recipient.slice(0, -1).map((line, i) => (
              <span key={line} className={i === 0 ? 'mb-[1.22em] block' : 'block'}>
                {line}
              </span>
            ))}
            {/* Typed with a space between letters, the way an envelope's country often was. */}
            <span aria-label={country} className="mt-[1.22em] block border-b border-current pb-px whitespace-pre">
              <span aria-hidden="true">{country.split(' ').map((word) => word.split('').join(' ')).join('   ')}</span>
            </span>
          </p>
        </div>

        <div className="mt-14 max-w-[64ch] sm:mt-24">
          <p>{salutation}</p>
          {body.map((paragraph, i) => (
            <p key={i} className={i === 0 ? '' : 'mt-[1.22em]'}>
              {paragraph.split(MARKS).map((part, j) => {
                if (j % 2 === 0) return <Linked key={j} text={part} />
                const red = part.startsWith('!!')
                return (
                  <mark key={j} className={red ? 'typed-mark typed-mark-red' : 'typed-mark'} style={{ '--mark': mark++ } as CSSProperties}>
                    <Linked text={part.slice(2, -2)} />
                  </mark>
                )
              })}
            </p>
          ))}

          <p className="mt-[1.22em]">{closing}</p>
          <p className="typed-signature mt-3 ml-2 -rotate-[5deg] text-[2.6em] leading-none sm:ml-6">{signature}</p>

          <dl className="mt-14 grid grid-cols-[auto_1fr] gap-x-[1ch] sm:mt-20">
            <dt>Encl.:</dt>
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
