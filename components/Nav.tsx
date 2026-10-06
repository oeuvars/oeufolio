import NavClient, { type NavLink } from "./NavClient"
import { getGalleries } from "@/lib/data"
import { partField } from "@/lib/fields"
import type { FieldKey, ScreeningPart } from "@/lib/types"
import content from "@/data/homepage.json"
import general from "@/data/general.json"

// Server component: builds the links and the screening's parts from the
// configuration (galleries read from the file system + data/homepage.json) and
// hands the interactivity to NavClient.

type SectionKey = "galleries" | "articles" | "exhibitions-cta" | "about" | "contact"
type SectionLink = NavLink & { section: SectionKey }

const visibility = content.sectionVisibility as Partial<Record<SectionKey, boolean>>
const sectionOrder = content.sectionOrder as SectionKey[]

const sectionIndex = (key: SectionKey) => {
  const i = sectionOrder.indexOf(key)
  return i === -1 ? Infinity : i
}

function buildLinks(): NavLink[] {
  // One entry per public gallery, pointing at its own page
  const galleryLinks: SectionLink[] = getGalleries()
    .filter((g) => g.config.visibility === "public")
    .map((g) => ({ href: `/galleries/${g.id}`, label: g.title, section: "galleries" }))

  const baseLinks: SectionLink[] = [
    ...galleryLinks,
    { href: "#about",       label: "About",       section: "about" },
    { href: "#elsewhere",   label: "Elsewhere",   section: "about" },
    { href: "#contact",     label: "Contact",     section: "contact" },
    { href: "/exhibitions", label: "Exhibitions", section: "exhibitions-cta" },
  ]

  return baseLinks
    .filter((l) => visibility[l.section] === true)
    .sort((a, b) => {
      const diff = sectionIndex(a.section) - sectionIndex(b.section)
      if (diff !== 0) return diff
      return baseLinks.indexOf(a) - baseLinks.indexOf(b)
    })
    .map(({ href, label }) => ({ href, label }))
}

// Every still of every public gallery, in order: what Play runs through.
function buildParts(): ScreeningPart[] {
  return getGalleries()
    .filter((g) => g.config.visibility === "public")
    .flatMap((g) =>
      g.works.map((work, i) => ({
        title: work.title ?? work.alt,
        note: work.note,
        src: `/assets/${work.file}`,
        alt: work.alt,
        field: partField(work.field, i),
        focus: work.focus,
      })),
    )
}

// `field` is the field of the first card on the page, so the bar is the right
// colour before the client takes over.
export default function Nav({ field = "cream" }: { field?: FieldKey }) {
  return <NavClient links={buildLinks()} brand={general.artistName} parts={buildParts()} initialField={field} />
}
