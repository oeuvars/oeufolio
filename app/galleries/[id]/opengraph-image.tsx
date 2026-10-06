import { ImageResponse } from "next/og"
import { getGalleries } from "@/lib/data"
import { firstUsableDataUri } from "@/lib/ogAssets"
import general from "@/data/general.json"

export const size = { width: 1200, height: 630 }
export const contentType = "image/png"
export const alt = `Stills by ${general.artistName}`

interface OgImageProps {
  params: Promise<{ id: string }>
}

// Without generateStaticParams the route would stay dynamic: on Vercel
// public/assets is not in the function bundle at runtime, so the image has to
// be generated at build time.
export function generateStaticParams(): { id: string }[] {
  return getGalleries().map((gallery) => ({ id: gallery.id }))
}

// Colours: the cream field of app/globals.css written out as hex (see app/opengraph-image.tsx)
export default async function OpengraphImage({ params }: OgImageProps) {
  const { id } = await params
  const gallery = getGalleries().find((g) => g.id === id)
  const imageSrc = gallery
    ? firstUsableDataUri(gallery.works.map((w) => w.file))
    : null

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          backgroundColor: "#f1e4c6",
        }}
      >
        {imageSrc && (
          <img
            src={imageSrc}
            alt=""
            style={{ width: "50%", height: "100%", objectFit: "cover" }}
          />
        )}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: 64,
          }}
        >
          <div style={{ fontSize: 56, color: "#1e1a16", lineHeight: 1.1, textTransform: "uppercase", letterSpacing: 3 }}>
            {gallery?.title ?? "Stills"}
          </div>
          {gallery?.subtitle && (
            <div style={{ fontSize: 26, color: "#1e1a16", marginTop: 16 }}>
              {gallery.subtitle}
            </div>
          )}
          <div style={{ fontSize: 28, color: "#1e1a16", marginTop: 28 }}>
            {general.siteTitle}
          </div>
        </div>
      </div>
    ),
    size,
  )
}
