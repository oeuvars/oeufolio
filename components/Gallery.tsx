'use client'

import { useState } from "react"
import Image from "next/image"
import type { GallerySection } from "@/lib/data"
import { filterByMedium, uniqueMediums } from "@/lib/mediums"
import { screeningSeconds } from "@/lib/screening"
import { countWord } from "@/lib/words"
import Lightbox from "./Lightbox"
import MediumFilter from "./MediumFilter"
import { PlayCard } from "./PlayButton"

interface GalleryProps {
  section: GallerySection
  // Show the filter chips by medium
  enableFilter?: boolean
  // Close the grid with the Play card
  enablePlay?: boolean
}

// A gallery on its own page: every still in the same window, in a grid, with
// its number, title and note. A still opens uncropped in the lightbox.
// The homepage shows the same works one per card (components/Parts.tsx).
export default function Gallery({ section, enableFilter = false, enablePlay = false }: GalleryProps) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [activeMedium, setActiveMedium] = useState<string | null>(null)

  const mediums = enableFilter ? uniqueMediums(section.works) : []
  const works = enableFilter ? filterByMedium(section.works, activeMedium) : section.works
  const handleFilterChange = (medium: string | null) => {
    setActiveMedium(medium)
    setLightboxIndex(null) // indexes change with the filter
  }
  // "masonry" has no place among fixed windows: it lays out as three columns.
  const layout = section.config.layout === "grid-2" ? "grid-2" : "grid-3"
  const sizes =
    layout === "grid-2"
      ? "(max-width: 640px) 90vw, 420px"
      : "(max-width: 640px) 90vw, (max-width: 900px) 45vw, 350px"

  return (
    <>
      <section id={section.id} className="card f-cream" data-field="cream">
        <div className="stage stage-page">
          {section.subtitle && <p className="label">{section.subtitle}</p>}
          <h1 className="title title-page">{section.title}</h1>
          {enableFilter && (
            <div className="mt-8">
              <MediumFilter media={mediums} active={activeMedium} onChange={handleFilterChange} />
            </div>
          )}
          <ul className="still-grid" data-layout={layout}>
            {works.map((work, i) => {
              const title = work.title ?? work.alt
              return (
                <li key={work.file}>
                  <button type="button" className="frame" onClick={() => setLightboxIndex(i)} aria-label={`Open ${title}`}>
                    <Image
                      src={work.blurDataURL ? `/assets-opt/${work.file}` : `/assets/${work.file}`}
                      alt={work.alt}
                      fill
                      sizes={sizes}
                      style={work.focus ? { objectPosition: work.focus } : undefined}
                      {...(work.blurDataURL && { placeholder: "blur" as const, blurDataURL: work.blurDataURL })}
                    />
                  </button>
                  <div className="cell-caption">
                    <p className="cell-title">{i + 1}. {title}</p>
                    {work.note && <p className="cell-note">{work.note}</p>}
                  </div>
                </li>
              )
            })}
            {enablePlay && works.length > 0 && (
              <li>
                <PlayCard
                  label={works.length === 1 ? "Play it" : `Play all ${countWord(works.length)}`}
                  detail={`${screeningSeconds(works.length)} seconds`}
                />
              </li>
            )}
          </ul>
        </div>
      </section>

      {/* Outside the card: a card is its own stacking context, and the lightbox
          has to cover the fixed header as well. */}
      {lightboxIndex !== null && (
        <Lightbox works={works} initialIndex={lightboxIndex} onClose={() => setLightboxIndex(null)} />
      )}
    </>
  )
}
