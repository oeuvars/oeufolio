import { cv, profile } from '../../content'
import { code128 } from '../../lib/code128'

// The label is drawn on a 400 by 600 grid, a 4 by 6 inch thermal label at a hundred to the inch, and scales with its
// width: one unit is a quarter of a container width percent.
const u = (n: number) => `${n * 0.25}cqw`

const FIELD = 'block leading-none font-semibold [font-stretch:75%]'
const RULE = 'border-t-[3px] border-black'

/** The barcode of the email, drawn module by module, with the ten-module quiet zone either side Code 128 asks for. */
function Barcode({ text }: { text: string }) {
  const { bars, width } = code128(text)
  const quiet = 10
  return (
    <svg
      aria-hidden="true"
      viewBox={`0 0 ${width + 2 * quiet} 1`}
      preserveAspectRatio="none"
      shapeRendering="crispEdges"
      className="block w-full"
      style={{ height: u(72) }}
    >
      {bars.map(([start, size]) => (
        <rect key={start} x={start + quiet} y="0" width={size} height="1" />
      ))}
    </svg>
  )
}

/**
 * The top of the résumé as a 4 by 6 shipping label addressed to me, the way Cybership's label system prints ten
 * thousand a day: who it is from, the address in capitals, the routing code of Kolkata's airport, the service with its
 * letter box, the email as a scannable barcode, and what the parcel holds. It prints on load, fed out a line at a time.
 */
export function Label() {
  const [first, last] = cv.name.toUpperCase().split(' ')
  const city = profile.extras.particulars.find((particular) => particular.label === 'Based in')?.value ?? ''

  return (
    <section
      aria-label="Shipping label"
      className="@container relative aspect-[2/3] w-full overflow-hidden rounded-[12px] bg-white text-black motion-safe:animate-[label-feed_1.4s_steps(36,end)_both] print:hidden"
    >
      <div className="flex h-full flex-col" style={{ padding: `${u(14)} ${u(16)}` }}>
        <div className="flex items-stretch justify-between" style={{ gap: u(12), paddingBottom: u(10) }}>
          <p style={{ paddingTop: u(4) }}>
            <span className={FIELD} style={{ fontSize: u(11) }}>
              From
            </span>
            <span className="mt-[0.35em] block leading-none font-bold" style={{ fontSize: u(17) }}>
              Your team
            </span>
          </p>
          <p
            className="flex items-center justify-center bg-black leading-none font-black text-white [font-stretch:80%]"
            style={{ fontSize: u(42), width: u(124), height: u(56), borderRadius: u(4) }}
          >
            <abbr title="Kolkata airport" className="no-underline">
              CCU
            </abbr>
          </p>
        </div>

        <div className={`${RULE} flex flex-1 flex-col`} style={{ paddingTop: u(10), paddingBottom: u(10) }}>
          <span className={FIELD} style={{ fontSize: u(11) }}>
            Ship to
          </span>
          <h1 className="mt-auto leading-[0.84] font-black tracking-[-0.02em] [font-stretch:112%]" style={{ fontSize: u(70) }}>
            {first}
            <br />
            {last}
          </h1>
          <p lang="hi" className="font-medium" style={{ fontSize: u(18), marginTop: u(10) }}>
            अनुराग दास
          </p>
          <p className="leading-tight font-bold tracking-[0.01em] uppercase" style={{ fontSize: u(17) }}>
            {city}
          </p>
        </div>

        <div className={`${RULE} flex items-center justify-between`} style={{ gap: u(12), paddingTop: u(8), paddingBottom: u(8) }}>
          <p>
            <span className={FIELD} style={{ fontSize: u(11) }}>
              Service
            </span>
            <span className="mt-[0.2em] block leading-none font-extrabold [font-stretch:80%]" style={{ fontSize: u(28) }}>
              Product engineer
            </span>
          </p>
          <span
            aria-hidden="true"
            className="flex shrink-0 items-center justify-center bg-black leading-none font-black text-white"
            style={{ fontSize: u(46), width: u(54), height: u(54), borderRadius: u(4) }}
          >
            P
          </span>
        </div>

        <a
          href={`mailto:${profile.email}`}
          aria-label={`Email ${profile.email}`}
          className={`${RULE} group block outline-none focus-visible:bg-[#f5e34a]`}
          style={{ paddingTop: u(10), paddingBottom: u(8), borderTopWidth: u(6) }}
        >
          <span className={FIELD} style={{ fontSize: u(11), marginBottom: u(8) }}>
            Tracking
          </span>
          <Barcode text={profile.email} />
          <span
            className="block text-center leading-none font-semibold tracking-[0.18em] tabular-nums group-hover:underline"
            style={{ fontSize: u(15), marginTop: u(8) }}
          >
            {profile.email}
          </span>
        </a>

        <div className={RULE} style={{ paddingTop: u(9) }}>
          <span className={FIELD} style={{ fontSize: u(11) }}>
            Contents
          </span>
          <p className="leading-snug font-medium" style={{ fontSize: u(14), marginTop: u(5) }}>
            Automation Rules, Cybership Desktop, Shipping Labels, Altern8
          </p>
        </div>
      </div>
    </section>
  )
}
