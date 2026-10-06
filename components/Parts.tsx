import Link from "next/link"
import Still from "./Still"
import type { GallerySection } from "@/lib/data"
import { partField } from "@/lib/fields"

interface PartsProps {
  section: GallerySection
  // Preview mode: show only the first N parts…
  previewCount?: number
  // …with a link to the gallery's own page for the rest
  detailHref?: string
}

// A gallery on the homepage: every work is a part, one card each, on its own
// field. The gallery's page (components/Gallery.tsx) shows them as a grid.
export default function Parts({ section, previewCount, detailHref }: PartsProps) {
  const works = previewCount !== undefined ? section.works.slice(0, previewCount) : section.works
  const hasMore = detailHref !== undefined && works.length < section.works.length

  return works.map((work, i) => {
    const field = partField(work.field, i)
    const isLast = i === works.length - 1
    return (
      <section
        key={work.file}
        id={`${section.id}-${i + 1}`}
        className={`card f-${field}`}
        data-field={field}
      >
        <div className="stage">
          <p className="label">
            Part {i + 1} of {works.length}
          </p>
          <h2 className="title">{work.title ?? work.alt}</h2>
          <Still
            src={work.blurDataURL ? `/assets-opt/${work.file}` : `/assets/${work.file}`}
            alt={work.alt}
            note={work.note}
            focus={work.focus}
            sizes="(max-width: 640px) 90vw, (max-width: 1100px) 90vw, 700px"
            blurDataURL={work.blurDataURL}
          />
        </div>
        <p className="label tail">
          {!isLast && <a href={`#${section.id}-${i + 2}`}>Next, part {i + 2}</a>}
          {isLast && hasMore && <Link href={detailHref}>See all of {section.title}</Link>}
          {isLast && !hasMore && "The end"}
        </p>
      </section>
    )
  })
}
