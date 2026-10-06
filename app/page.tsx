import React from "react"
import Nav from "@/components/Nav"
import Hero, { HERO_FIELD } from "@/components/Hero"
import Parts from "@/components/Parts"
import About from "@/components/About"
import Contact from "@/components/Contact"
import Footer from "@/components/Footer"
import ArticleBlock from "@/components/Article"
import ExhibitionsCta from "@/components/ExhibitionsCta"
import FeaturedWorks from "@/components/FeaturedWorks"
import { getGalleries, getHeroImages, getArticles, getExhibitions, getFeaturedWorks } from "@/lib/data"
import { getExhibitionStatus, statusBadgeLabel } from "@/lib/exhibitionStatus"
import content from "@/data/homepage.json"

type SectionKey = "galleries" | "about" | "contact" | "articles" | "exhibitions-cta" | "featured"
const DEFAULT_ORDER: SectionKey[] = ["galleries", "about", "contact"]

// The text sections the template ships (articles, exhibitions, featured,
// contact) sit on the cream field when switched on.
function CreamCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="card f-cream" data-field="cream">
      <div className="pt-24">{children}</div>
    </div>
  )
}

export default function Home() {
  const galleries = getGalleries().filter((section) => section.config.visibility === "public")
  const heroImages = getHeroImages()
  const articles = getArticles()
  const featuredWorks = getFeaturedWorks()
  const allExhibitions = getExhibitions()
  const homepageExhibitions = allExhibitions.filter(e => e.showInHomepage)

  // The "live" exhibition: one in progress, otherwise the nearest upcoming.
  // getExhibitions() is sorted by date desc → among the upcoming, the last is the nearest.
  const liveEntries = allExhibitions
    .map((e) => ({ e, status: getExhibitionStatus(e.date, e.dateEnd) }))
    .filter((x) => x.status === "current" || x.status === "upcoming")
  const livePick = liveEntries.find((x) => x.status === "current") ?? liveEntries[liveEntries.length - 1]
  const liveLabel = livePick ? statusBadgeLabel(livePick.status, livePick.e.date, livePick.e.dateEnd) : null
  const liveBadge = livePick && liveLabel ? { title: livePick.e.title, label: liveLabel } : undefined
  const rawOrder = (content.sectionOrder as SectionKey[] | undefined) ?? DEFAULT_ORDER
  const visibility = content.sectionVisibility as Partial<Record<SectionKey, boolean>> | undefined
  const order = rawOrder.filter((key) => visibility?.[key] === true)
  const partCount = visibility?.galleries === true
    ? galleries.reduce((sum, section) => sum + (section.config.enabled ? Math.min(section.config.limitItems, section.works.length) : section.works.length), 0)
    : 0

  const sectionMap: Record<SectionKey, React.ReactNode> = {
    galleries: galleries.map((section) => (
      <Parts
        key={section.id}
        section={section}
        previewCount={section.config.enabled ? section.config.limitItems : undefined}
        detailHref={section.config.enabled ? `/galleries/${section.id}` : undefined}
      />
    )),
    about: <About />,
    contact: <CreamCard><Contact /></CreamCard>,
    "exhibitions-cta": <CreamCard><ExhibitionsCta exhibitions={homepageExhibitions} live={liveBadge} /></CreamCard>,
    articles: articles.length > 0 ? (
      <CreamCard>
        <section id="articles" className="py-32 px-6">
          <div className="max-w-7xl mx-auto divide-y divide-rule">
            {articles.map((article) => (
              <ArticleBlock key={article.id} article={article} />
            ))}
          </div>
        </section>
      </CreamCard>
    ) : null,
    featured: <CreamCard><FeaturedWorks works={featuredWorks} /></CreamCard>,
  }

  // The footer strip continues the last card: teal under the credits, cream otherwise.
  const lastKey = order[order.length - 1]
  const footerField = lastKey === "about" ? "teal" : "cream"

  return (
    <>
      <Nav field={HERO_FIELD} />
      <main>
        <Hero images={heroImages} partCount={partCount} />
        {order.map((key) => (
          <React.Fragment key={key}>{sectionMap[key]}</React.Fragment>
        ))}
      </main>
      <Footer field={footerField} />
    </>
  )
}
