import { marked } from "marked"
import Link from "next/link"
import Still from "./Still"
import content from "@/data/bio.json"
import homepage from "@/data/homepage.json"
import general from "@/data/general.json"
import { getGalleries, getHeroImages, getMostre, getPremi, type TimelineEntry } from "@/lib/data"
import type { SocialKey } from "@/lib/types"

function groupByYear(items: TimelineEntry[]) {
  const sorted = [...items].sort((a, b) => b.year.localeCompare(a.year))
  const groups: { year: string; descriptions: string[] }[] = []
  for (const item of sorted) {
    const last = groups[groups.length - 1]
    if (last && last.year === item.year) {
      last.descriptions.push(item.description)
    } else {
      groups.push({ year: item.year, descriptions: [item.description] })
    }
  }
  return groups
}

// Explicit types: a field cleared in the CMS can vanish from the JSON, and the
// type inferred from the file would then break the build.
const bio = content as {
  bio: string
  location?: string
  occupation?: string
  social: Partial<Record<SocialKey, string>>
  aboutSections: { biografia?: boolean; mostre?: boolean; premi?: boolean }
}
const hero = homepage.hero as { alt?: string; credit?: string; focus?: string }

const SOCIAL_LABELS: [SocialKey, string][] = [
  ["github", "GitHub"],
  ["instagram", "Instagram"],
  ["x", "X"],
  ["facebook", "Facebook"],
  ["website", "Also at"],
]

// What a link reads as on the card: the handle for a profile, the host for a site.
function linkText(key: SocialKey, url: string): string {
  try {
    const parsed = new URL(url)
    if (key === "website") return parsed.hostname.replace(/^www\./, "")
    return parsed.pathname.split("/").filter(Boolean).pop() ?? parsed.hostname
  } catch {
    return url
  }
}

const socialLinks = SOCIAL_LABELS.flatMap(([key, label]) => {
  const url = bio.social[key]
  return url ? [{ key, label, url, text: linkText(key, url) }] : []
})

const facts = [
  { label: "Based in", value: bio.location },
  { label: "Works as", value: bio.occupation },
].filter((fact) => fact.value)

const { aboutSections: s } = bio

// The credits card: who, where, the outbound links, and every still with the
// photographer who made it.
export default async function About() {
  const mostreItems = getMostre()
  const premiItems = getPremi()
  const heroImage = getHeroImages().desktop[0]
  const galleries = getGalleries().filter((g) => g.config.visibility === "public")

  return (
    <section id="about" className="card f-teal" data-field="teal" data-named>
      <div className="stage stage-page">
        <p className="label">About</p>
        <h2 className="title title-page">{general.artistName}</h2>

        {s.biografia === true && (
          <div
            className="credits-line"
            dangerouslySetInnerHTML={{ __html: marked.parse(bio.bio, { breaks: true }) as string }}
          />
        )}

        <dl id="elsewhere" className="roll">
          {facts.map((fact) => (
            <div key={fact.label} className="contents">
              <dt>{fact.label}</dt>
              <dd>{fact.value}</dd>
            </div>
          ))}
          {facts.length > 0 && socialLinks.length > 0 && <div className="roll-gap" />}
          {socialLinks.map(({ key, label, url, text }) => (
            <div key={key} className="contents">
              <dt>{label}</dt>
              <dd>
                <a href={url} target="_blank" rel="noopener noreferrer">{text}</a>
              </dd>
            </div>
          ))}
          {s.premi === true && premiItems.length > 0 && (
            <>
              <div className="roll-gap" />
              {groupByYear(premiItems).map((group) => (
                <div key={`premi-${group.year}`} className="contents">
                  <dt>Awards, {group.year}</dt>
                  <dd>{group.descriptions.map((desc, j) => <p key={j}>{desc}</p>)}</dd>
                </div>
              ))}
            </>
          )}
          {s.mostre === true && mostreItems.length > 0 && (
            <>
              <div className="roll-gap" />
              {groupByYear(mostreItems).map((group) => (
                <div key={`mostre-${group.year}`} className="contents">
                  <dt>Shown, {group.year}</dt>
                  <dd>{group.descriptions.map((desc, j) => <p key={j}>{desc}</p>)}</dd>
                </div>
              ))}
            </>
          )}
        </dl>

        <ul className="cast">
          {heroImage && (
            <li>
              <Link href="/#opening">
                <Still src={`/assets/${heroImage}`} alt={hero.alt ?? ""} focus={hero.focus} sizes="(max-width: 640px) 45vw, 180px" />
                <b>Opening</b>
                {hero.credit && <small>Still by {hero.credit}</small>}
              </Link>
            </li>
          )}
          {galleries.flatMap((gallery) =>
            gallery.works.map((work) => (
              <li key={work.file}>
                <Link href={`/galleries/${gallery.id}`}>
                  <Still
                    src={work.blurDataURL ? `/assets-opt/${work.file}` : `/assets/${work.file}`}
                    alt={work.alt}
                    focus={work.focus}
                    sizes="(max-width: 640px) 45vw, 180px"
                    blurDataURL={work.blurDataURL}
                  />
                  <b>{work.title ?? work.alt}</b>
                  {work.credit && <small>Still by {work.credit}</small>}
                </Link>
              </li>
            )),
          )}
        </ul>
      </div>
    </section>
  )
}
