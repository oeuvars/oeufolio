import { Link } from '@tanstack/react-router'

import { profile } from '../content'
import { Label } from './waybill/Label'
import { Slip } from './waybill/Slip'

// The box the label is stuck on: plain corrugated kraft, flat, with nothing drawn on it.
const KRAFT = '#bf9465'
const LINK = 'underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black'

/**
 * The résumé as a parcel: a shipping label addressed to me, the kind of label my work at Cybership prints, and the
 * packing slip that carries the résumé in full. On a wide window the label stays in view beside the slip.
 */
export function Waybill() {
  const links = [...profile.socials, { label: 'resume.pdf', href: profile.resume.href }]

  return (
    <div
      className="min-h-screen w-full font-['Archivo_Variable',sans-serif] text-black antialiased print:bg-white"
      style={{ backgroundColor: KRAFT }}
    >
      <div className="mx-auto grid max-w-[1180px] gap-8 px-4 py-6 sm:px-8 sm:py-10 lg:grid-cols-[minmax(0,min(420px,calc((100vh-9rem)*2/3)))_minmax(0,1fr)] lg:items-start lg:gap-12">
        <div className="mx-auto w-full max-w-[420px] lg:sticky lg:top-10 print:hidden">
          <Label />
          <nav aria-label="Elsewhere" className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-[14px] font-semibold">
            {links.map((link) => (
              <a key={link.label} href={link.href} target="_blank" rel="noopener" className={LINK}>
                {link.label}
              </a>
            ))}
            <Link to="/" className={`${LINK} ml-auto`}>
              Back to the site
            </Link>
          </nav>
        </div>
        <Slip />
      </div>
    </div>
  )
}
