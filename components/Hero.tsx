import Still from "./Still"
import type { HeroImages } from "@/lib/data"
import { isFieldKey } from "@/lib/fields"
import { countWord } from "@/lib/words"
import content from "@/data/homepage.json"

// Explicit type: a field cleared in the CMS can vanish from the JSON, and the
// type inferred from homepage.json would then break the build.
const hero = content.hero as {
  name: string
  subtitle?: string
  label?: string
  alt?: string
  field?: string
  focus?: string
}

export const HERO_FIELD = isFieldKey(hero.field) ? hero.field : "pink"

// The opening card: the name as the title, the first still, the site's line as
// its subtitle.
export default function Hero({ images, partCount }: { images: HeroImages; partCount: number }) {
  const desktop = images.desktop[0] ?? images.mobile[0]
  const mobile = images.mobile[0] ?? images.desktop[0]
  const alt = hero.alt ?? ""

  return (
    <section id="opening" className={`card f-${HERO_FIELD}`} data-field={HERO_FIELD} data-named>
      <div className="stage">
        {hero.label && <p className="label">{hero.label}</p>}
        <h1 className="title title-xl">{hero.name}</h1>
        {/* Wide screens (≥640px) and phones take separate crops */}
        {desktop && (
          <Still
            className="max-sm:hidden"
            src={`/assets/${desktop}`}
            alt={alt}
            note={hero.subtitle}
            focus={hero.focus}
            sizes="(max-width: 1100px) 90vw, 700px"
            eager
          />
        )}
        {mobile && (
          <Still
            className="sm:hidden"
            src={`/assets/${mobile}`}
            alt={alt}
            note={hero.subtitle}
            focus={hero.focus}
            sizes="90vw"
            eager
          />
        )}
      </div>
      {partCount > 0 && (
        <p className="label tail">
          In {countWord(partCount)} {partCount === 1 ? "part" : "parts"}
        </p>
      )}
    </section>
  )
}
