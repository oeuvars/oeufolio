
import notFoundCss from './not-found.css?url'

const HAZARD = ['SIGNAL LOST', '信号なし', 'ERR 404', 'PAGE NOT FOUND', 'ページが見つかりません']
const BREACH = ['NO SUCH ROUTE', '0x194', 'DEAD LINK', 'エラー']

/** One line of tape's printing, set twice end to end so that it runs round without a seam. */
function Track({ words }: { words: string[] }) {
  const line = Array.from({ length: 4 }, () => words).flat()
  return (
    <div className="nf-track">
      {[0, 1].map((copy) => (
        <span key={copy} aria-hidden={copy === 1 || undefined}>
          {line.map((word, i) => (
            <span key={i} className="nf-track-word">
              {word}
            </span>
          ))}
        </span>
      ))}
    </div>
  )
}

/** The page for a path that is not one: a 404 pasted up on a wall at night, out of photocopies, tape and spray paint. */
export function NotFound() {
  return (
    <main className="nf">
      {/* Only this page loads its styles and faces. React lifts the link into the head. */}
      <link rel="stylesheet" href={notFoundCss} precedence="default" />
      <svg aria-hidden width="0" height="0" className="absolute">
        <defs>
          {/* Toner on a photocopy: the edge chewed, then flecks where it did not take. */}
          <filter id="nf-distress" x="-5%" y="-5%" width="110%" height="110%" colorInterpolationFilters="sRGB">
            <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="4" result="warp" />
            <feDisplacementMap in="SourceGraphic" in2="warp" scale="9" xChannelSelector="R" yChannelSelector="G" result="rough" />
            <feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="2" seed="12" result="specks" />
            <feColorMatrix in="specks" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -14 9.6" result="holes" />
            <feComposite in="rough" in2="holes" operator="in" />
          </filter>
          {/* Paint from a can: a cloud with a ragged rim. */}
          <filter id="nf-spray" x="-30%" y="-30%" width="160%" height="160%">
            <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="4" seed="9" result="warp" />
            <feDisplacementMap in="SourceGraphic" in2="warp" scale="120" xChannelSelector="R" yChannelSelector="B" result="cloud" />
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed="2" result="mist" />
            <feColorMatrix in="mist" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.6" result="dots" />
            <feComposite in="cloud" in2="dots" operator="in" />
          </filter>
          {/* Ink that bled into the paper. */}
          <filter id="nf-bleed" x="-10%" y="-10%" width="120%" height="120%">
            <feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="2" seed="21" result="edge" />
            <feDisplacementMap in="SourceGraphic" in2="edge" scale="2.4" xChannelSelector="R" yChannelSelector="G" />
          </filter>
        </defs>
      </svg>

      {/* The wall: stains, a halftone wash, a grid, and two gels of light. */}
      <div aria-hidden className="nf-wall" />
      <div aria-hidden className="nf-halftone" />
      <div aria-hidden className="nf-grid" />
      <div aria-hidden className="nf-spray nf-spray-hot" />
      <div aria-hidden className="nf-spray nf-spray-cold" />

      {/* Print marks, as if the wall were the proof. */}
      {(['tl', 'tr', 'bl', 'br'] as const).map((corner) => (
        <span key={corner} aria-hidden className={`nf-crop nf-crop-${corner}`} />
      ))}
      <span aria-hidden className="nf-target nf-target-l" />
      <span aria-hidden className="nf-target nf-target-r" />

      <span aria-hidden className="nf-barcode" />

      <h1 className="nf-code" aria-label="404, page not found">
        <span aria-hidden className="nf-layer nf-stroke">
          404
        </span>
        <span aria-hidden className="nf-layer nf-red">
          404
        </span>
        <span aria-hidden className="nf-layer nf-cyan">
          404
        </span>
        <span aria-hidden className="nf-layer nf-face">
          404
        </span>
        <span aria-hidden className="nf-layer nf-face nf-slice nf-slice-a">
          404
        </span>
        <span aria-hidden className="nf-layer nf-face nf-slice nf-slice-b">
          404
        </span>
      </h1>

      <p aria-hidden className="nf-scrawl">
        dead end.
      </p>

      <div aria-hidden className="nf-tape nf-tape-breach">
        <Track words={BREACH} />
      </div>
      <div aria-hidden className="nf-tape nf-tape-hazard">
        <Track words={HAZARD} />
      </div>

      {/* Over everything: the screen's lines, its grain and its dark corners. */}
      <div aria-hidden className="nf-scanlines" />
      <div aria-hidden className="nf-grain" />
      <div aria-hidden className="nf-vignette" />
    </main>
  )
}
