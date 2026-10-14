import '@fontsource/playfair-display/900.css'

import { profile } from '../../content'
import { code128 } from './barcode'
import ticket from './ticket.json'

type PrintProps = {
  /** Copies the email address. The field the conductor punches. */
  onCopy: () => void
  copied: boolean
}

const [, , ARTW, ARTH] = ticket.art
const BARS = code128(profile.email)

/** A field as the ticket prints it: its name in small capitals, then a colon, and under it what it holds. */
function Field({ label, children, className = '' }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`absolute ${className}`}>
      <p className="font-mono text-[0.55em] leading-none font-bold tracking-[0.14em] uppercase">{label} :</p>
      <div className="mt-[0.32em] font-mono leading-none font-medium">{children}</div>
    </div>
  )
}

/** One of the three little umbrellas that stand by the title, as the reference's do. */
function Umbrella({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} 0)`}>
      <path d="M0 5.2 Q0.6 0.6 5 0.4 Q9.4 0.6 10 5.2 Q8.75 4.2 7.5 5.2 Q6.25 4.2 5 5.2 Q3.75 4.2 2.5 5.2 Q1.25 4.2 0 5.2Z" />
      <path d="M4.6 0.4h0.8v8.2q0 1.6-1.6 1.6t-1.6-1.6h0.8q0 0.8 0.8 0.8t0.8-0.8z" />
    </g>
  )
}

/**
 * What is printed on the ticket, set in its own em: the ticket is 15 em by 31. The same type is the plate
 * studio/ticket/ticket.py presses into the card, and, laid over the photograph of it and left clear, what a
 * visitor selects and follows. So the links are where their words are printed. The picture, the umbrellas
 * and the barcode are only ink: they show on the plate and not on the page, where the photograph has them.
 */
export function Print({ onCopy, copied }: PrintProps) {
  const github = profile.socials.find((social) => social.label === 'GitHub')
  const x = profile.socials.find((social) => social.label === 'X')
  const linkedin = profile.socials.find((social) => social.label === 'LinkedIn')
  const handle = (href = '') => href.replace(/\/$/, '').split('/').pop()
  const value = 'cursor-pointer decoration-[#1a1916]/75 decoration-[0.07em] underline-offset-[0.2em] hover:underline focus-visible:underline focus-visible:outline-none'

  return (
    <>
      <div
        data-art
        aria-hidden
        className="ink-only absolute bg-contain bg-no-repeat"
        style={{ left: `${ticket.art[0]}em`, top: `${ticket.art[1]}em`, width: `${ARTW}em`, height: `${ARTH}em` }}
      />

      <div className="absolute top-[14.85em] left-[1em] w-[13em]">
        <div className="flex items-end justify-between">
          <h2 className="font-serif text-[1.6em] leading-none font-black tracking-[-0.01em] whitespace-nowrap">
            {profile.extras.name}
          </h2>
          <svg aria-hidden viewBox="0 0 34 10.2" className="ink-only mb-[0.15em] w-[2.6em] fill-current">
            <Umbrella x={0} />
            <Umbrella x={12} />
            <Umbrella x={24} />
          </svg>
        </div>
        <p className="mt-[0.3em] font-serif text-[0.86em] leading-none font-black">Oeuvars</p>
        <div className="mt-[0.65em] space-y-[0.45em] font-mono text-[0.6em] leading-none font-medium">
          <p>[India] Kolkata / Software Engineer</p>
          <p>Servers and interfaces / {profile.extras.company.label}</p>
        </div>
      </div>

      <Field label="Email" className="top-[20.25em] left-[1em]">
        <button type="button" onClick={onCopy} className={`${value} text-[1em]`} aria-label={`Copy ${profile.email}`}>
          {profile.email}
        </button>
        <span className="sr-only" aria-live="polite">
          {copied ? 'Copied' : ''}
        </span>
      </Field>

      <Field label="GitHub" className="top-[22.6em] left-[1em]">
        <a href={github?.href} target="_blank" rel="noreferrer" className={`${value} text-[0.86em]`}>
          {handle(github?.href)}
        </a>
      </Field>
      <Field label="X" className="top-[22.6em] left-[5.55em]">
        <a href={x?.href} target="_blank" rel="noreferrer" className={`${value} text-[0.86em]`}>
          {handle(x?.href)}
        </a>
      </Field>
      <Field label="LinkedIn" className="top-[22.6em] left-[10.1em]">
        <a href={linkedin?.href} target="_blank" rel="noreferrer" className={`${value} text-[0.86em]`}>
          {handle(linkedin?.href)}
        </a>
      </Field>

      <Field label="Venue" className="top-[24.8em] left-[1em]">
        <span className="text-[0.72em]">Kolkata, India</span>
      </Field>
      <Field label="Time" className="top-[24.8em] left-[8.2em]">
        <span className="text-[0.72em]">IST, UTC+5:30</span>
      </Field>

      <div className="absolute top-[27.5em] left-[0.85em] flex h-[2.1em] w-[1em] items-center justify-center">
        <p className="rotate-180 font-mono text-[0.5em] leading-none font-bold tracking-[0.2em] [writing-mode:vertical-rl]">ADMIT ONE</p>
      </div>
      <svg
        aria-hidden
        viewBox={`0 0 ${BARS.length} 1`}
        preserveAspectRatio="none"
        className="ink-only absolute top-[27.5em] left-[2.1em] h-[2.1em] w-[10.8em] fill-current"
        shapeRendering="crispEdges"
      >
        {BARS.map((bar, i) => (bar ? <rect key={i} x={i} width={1} height={1} /> : null))}
      </svg>
      <div className="absolute top-[27.5em] right-[0.85em] flex h-[2.1em] w-[1em] items-center justify-center">
        <p className="font-mono text-[0.5em] leading-none font-bold tracking-[0.2em] [writing-mode:vertical-rl]">Nº 000001</p>
      </div>
      <div className="ink-only absolute top-[29.85em] left-0 w-full text-center">
        <p className="font-mono text-[0.48em] leading-none font-medium tracking-[0.32em]">{profile.email.toUpperCase()}</p>
      </div>
    </>
  )
}
