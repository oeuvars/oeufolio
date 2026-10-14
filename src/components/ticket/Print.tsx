import '@fontsource/domine/700.css'
import '@fontsource/gochi-hand/400.css'
import '@fontsource/martel/900.css'
import '@fontsource/red-hat-mono/700.css'

import { profile } from '../../content'
import ticket from './ticket.json'

type PrintProps = {
  /** Copies the email address. The conductor punches the ticket beside it. */
  onCopy: () => void
  copied: boolean
}

const [W] = ticket.size
const [AX, AY, AW, AH] = ticket.art

/**
 * A field as these tickets print it: its name in heavy capitals, spaced out, and a colon; under it what it
 * holds, in the ticket's serif.
 */
function Field({ label, children, className = '' }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`absolute ${className}`}>
      <p className="font-['Red_Hat_Mono'] text-[0.6em] leading-none font-bold tracking-[0.13em] uppercase">{label} :</p>
      <div className="mt-[0.42em] font-['Domine'] text-[0.8em] leading-none font-bold">{children}</div>
    </div>
  )
}

/** A rule of round dots across the ticket. */
function Rule({ y }: { y: number }) {
  const from = 0.62
  const pitch = 0.3
  const count = Math.floor((W - 2 * from) / pitch)

  return (
    <svg aria-hidden className="ink-only absolute left-0 overflow-visible" style={{ top: `${y}em` }} width="1em" height="1em" viewBox="0 0 1 1">
      {Array.from({ length: count + 1 }, (_, i) => (
        <circle key={i} cx={from + i * pitch} cy={0} r={0.062} />
      ))}
    </svg>
  )
}

/** One of the three small cats that sit by the title, where the reference's own film has its umbrellas. */
function Cat({ x }: { x: number }) {
  return (
    <path
      transform={`translate(${x} 0)`}
      d="M2.1 11.6c-.9 0-1.4-.6-1.2-1.6.3-1.8 1-3.6 1.1-5.2-.6-.6-1-1.5-1-2.5 0-.6.1-1.2.4-1.7L1.2 0l1.6 1.2c.4-.2.9-.3 1.4-.3s1 .1 1.4.3L7.2 0l-.2 1.6c.3.5.4 1.1.4 1.7 0 1-.4 1.9-1 2.5.2 1.6.9 3.4 1.2 5.2.1.6 0 1-.3 1.3.9-.2 1.7-.9 2-2 .3-1.2-.1-2.4.4-3.3.3-.5 1-.4 1 .2-.1.8-.4 1.6-.3 2.6.2 2-1.2 3.6-3.4 3.8H2.1z"
    />
  )
}

/**
 * What is printed on the ticket, set in its own em: the ticket is 15 em by 29.6, laid out as the illustrated
 * cinema tickets it follows lay theirs out. The picture runs to the edges under the bites. Under it the title
 * in its own script with the year beside it, and the title again in Latin letters; a rule of dots; three lines
 * of credits; a second rule where the ticket is notched to tear; the fields; a last rule; and a line written in
 * by hand. The same type is the plate studio/ticket/ticket.py prints on the card, and, laid over the photograph
 * of it and left clear, what a visitor selects and follows, so the links are where their words are printed.
 * The picture, the cats and the rules are only ink: they show on the plate, and on the page the photograph has
 * them. The ticket is printed in four inks, as the picture is: what is marked data-ink is printed in that ink,
 * the rest in black.
 */
export function Print({ onCopy, copied }: PrintProps) {
  const github = profile.socials.find((social) => social.label === 'GitHub')
  const x = profile.socials.find((social) => social.label === 'X')
  const linkedin = profile.socials.find((social) => social.label === 'LinkedIn')
  const handle = (href = '') => href.replace(/\/$/, '').split('/').pop()
  const value = 'cursor-pointer decoration-[0.07em] underline-offset-[0.18em] hover:underline focus-visible:underline focus-visible:outline-none'

  return (
    <>
      <div
        data-art
        aria-hidden
        className="ink-only absolute bg-cover bg-center"
        style={{ left: `${AX}em`, top: `${AY}em`, width: `${AW}em`, height: `${AH}em` }}
      />

      <div className="absolute top-[15.95em] right-[0.85em] left-[0.85em]">
        <div className="flex items-end justify-between">
          <h2 className="flex items-baseline whitespace-nowrap">
            <span lang="sa" data-ink="red" className="font-['Martel'] text-[1.55em] leading-[1.2] font-black">
              अनुराग दास
            </span>
            <span data-ink="red" className="ml-[0.15em] font-['Domine'] text-[0.62em] font-bold">(2026)</span>
          </h2>
          <svg aria-hidden data-ink="teal" viewBox="0 0 39 13" className="ink-only mb-[0.35em] w-[2.6em] fill-current">
            <Cat x={0} />
            <Cat x={13.5} />
            <Cat x={27} />
          </svg>
        </div>
        <p className="mt-[0.1em] font-['Domine'] text-[0.78em] leading-none font-bold">{profile.extras.name}</p>
      </div>

      <div className="absolute top-[19.4em] left-[0.85em]">
        <div className="space-y-[0.45em] font-['Domine'] text-[0.66em] leading-none font-bold whitespace-nowrap">
          <p>
            [India] <span lang="sa" className="font-['Martel'] font-black">अनुराग दास</span> Oeuvars
          </p>
          <p>Software Engineer/Servers/Interfaces</p>
          <p>Mar/2025({profile.extras.company.label}) / Now Showing / IST</p>
        </div>
      </div>

      <Field label="GitHub" className="top-[23.0em] left-[0.85em]">
        <a href={github?.href} target="_blank" rel="noreferrer" className={value}>
          {handle(github?.href)}
        </a>
      </Field>
      <Field label="X" className="top-[23.0em] left-[5.75em]">
        <a href={x?.href} target="_blank" rel="noreferrer" className={value}>
          {handle(x?.href)}
        </a>
      </Field>
      <Field label="LinkedIn" className="top-[23.0em] left-[10.1em]">
        <a href={linkedin?.href} target="_blank" rel="noreferrer" className={value}>
          {handle(linkedin?.href)}
        </a>
      </Field>
      <Field label="Email" className="top-[25.05em] left-[0.85em]">
        <button type="button" onClick={onCopy} className={value} aria-label={`Copy ${profile.email}`}>
          {profile.email}
        </button>
        <span className="sr-only" aria-live="polite">
          {copied ? 'Copied' : ''}
        </span>
      </Field>

      {ticket.rules.map((y) => (
        <Rule key={y} y={y} />
      ))}

      <div className="absolute top-[27.45em] left-[0.85em]">
        <p className="font-['Gochi_Hand'] text-[1.02em] leading-none whitespace-nowrap">Take your time getting here.</p>
      </div>
    </>
  )
}
