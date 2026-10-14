import '@fontsource/domine/700.css'
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

/** A field's name as these tickets print it: heavy capitals, spaced out, and a colon. */
function Label({ children, className = '', style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
  return (
    <p className={`font-['Red_Hat_Mono'] text-[0.6em] leading-none font-bold tracking-[0.13em] uppercase ${className}`} style={style}>
      {children} :
    </p>
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

/**
 * What is printed on the ticket, set in its own em: the ticket is 15 em by 27.45, laid out as the illustrated
 * cinema tickets it follows lay theirs out. The picture runs to the edges under the bites. Under it the title
 * in its own script with the year beside it, and the title again in Latin letters; a rule of dots where the
 * ticket is notched to tear; the fields, which are only the ways to reach me, each link a cat printed where its
 * username would be (studio/ticket/cats.py, only in the photograph: here each is a link over its cat), and the
 * email address on one line; a last rule; and a note written by
 * hand (studio/ticket/hand.py, only in the photograph: here it is for screen readers). The same type is
 * the plate studio/ticket/ticket.py prints on the card, and, laid over the photograph of it and left clear, what a
 * visitor selects and follows, so the links are where their words are printed. The picture and the rules are only
 * ink: they show on the plate, and on the page the photograph has them. The ticket is printed in four inks, as the
 * picture is: what is marked data-ink is printed in that ink, the rest in black.
 */
export function Print({ onCopy, copied }: PrintProps) {
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
        <h2 className="flex items-baseline whitespace-nowrap">
          <span lang="sa" data-ink="red" className="font-['Martel'] text-[1.55em] leading-[1.2] font-black">
            अनुराग दास
          </span>
          <span data-ink="red" className="ml-[0.15em] font-['Domine'] text-[0.62em] font-bold">(2026)</span>
        </h2>
        <p className="mt-[0.1em] font-['Domine'] text-[0.78em] leading-none font-bold">{profile.extras.name}</p>
      </div>

      {ticket.cats.map(({ link, label: [lx, ly], box: [bx, by, bw, bh] }) => {
        const social = profile.socials.find((entry) => entry.label === link)

        return (
          <div key={link}>
            {/* The label is set in its own smaller em, so its offsets are divided by that size. */}
            <Label className="absolute" style={{ left: `${lx / 0.6}em`, top: `${ly / 0.6}em` }}>
              {link}
            </Label>
            <a
              href={social?.href}
              target="_blank"
              rel="noreferrer"
              aria-label={`${link}: ${social?.href.split('/').pop()}`}
              className="absolute cursor-pointer rounded-[0.2em] focus-visible:outline-[0.08em] focus-visible:outline-offset-[0.1em] focus-visible:outline-current focus-visible:outline-dashed"
              style={{ left: `${bx}em`, top: `${by}em`, width: `${bw}em`, height: `${bh}em` }}
            />
          </div>
        )
      })}

      <div className="absolute top-[22.5em] left-[0.85em] flex items-baseline gap-[0.5em]">
        <Label>Email</Label>
        <button type="button" onClick={onCopy} className={`font-['Domine'] text-[0.8em] leading-none font-bold ${value}`} aria-label={`Copy ${profile.email}`}>
          {profile.email}
        </button>
        <span className="sr-only" aria-live="polite">
          {copied ? 'Copied' : ''}
        </span>
      </div>

      <p className="sr-only">Come say hello, any time. Or write a note, ask anything, tell me what the weather is like where you are.</p>

      {ticket.rules.map((y) => (
        <Rule key={y} y={y} />
      ))}

    </>
  )
}
