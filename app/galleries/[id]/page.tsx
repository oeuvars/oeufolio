import type { Metadata } from "next"
import { notFound } from "next/navigation"
import Nav from "@/components/Nav"
import Footer from "@/components/Footer"
import Gallery from "@/components/Gallery"
import { JsonLd } from "@/components/JsonLd"
import { buildVisualArtworkSchema } from "@/lib/jsonld"
import { getGalleries } from "@/lib/data"
import general from "@/data/general.json"

// Next 16: params is a Promise and has to be awaited.
interface GalleryPageProps {
  params: Promise<{ id: string }>
}

export function generateStaticParams(): { id: string }[] {
  return getGalleries().map((gallery) => ({ id: gallery.id }))
}

export async function generateMetadata({ params }: GalleryPageProps): Promise<Metadata> {
  const { id } = await params
  const gallery = getGalleries().find((g) => g.id === id)
  if (!gallery) return {}
  const count = gallery.works.length
  return {
    title: `${gallery.title} | ${general.artistName}`,
    description: `${gallery.title}: ${count} ${count === 1 ? "still" : "stills"} by ${general.artistName}.`,
  }
}

export default async function GalleryPage({ params }: GalleryPageProps) {
  const { id } = await params
  const gallery = getGalleries().find((g) => g.id === id)
  if (!gallery) notFound()

  return (
    <>
      <Nav field="cream" />
      <main>
        <JsonLd data={gallery.works.map((work) => buildVisualArtworkSchema(work, gallery))} />
        <Gallery section={gallery} enableFilter enablePlay />
      </main>
      <Footer field="cream" />
    </>
  )
}
