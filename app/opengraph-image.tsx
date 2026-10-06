import { ImageResponse } from "next/og"
import { getGalleries, getHeroImages } from "@/lib/data"
import { firstUsableDataUri } from "@/lib/ogAssets"
import general from "@/data/general.json"
import homepage from "@/data/homepage.json"

export const size = { width: 1200, height: 630 }
export const contentType = "image/png"
export const alt = `${general.artistName}: ${homepage.hero.subtitle}`

// The colours repeat the opening card's field in app/globals.css (pink
// #f1b8c4, plum #4e1a3a): CSS tokens do not exist in satori, so the values are
// written out.
export default function OpengraphImage() {
  const imageSrc = firstUsableDataUri([
    ...getHeroImages().desktop,
    ...getGalleries().flatMap((g) => g.works.map((w) => w.file)),
  ])

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          backgroundColor: "#f1b8c4",
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
          <div style={{ fontSize: 64, color: "#4e1a3a", lineHeight: 1.1, textTransform: "uppercase", letterSpacing: 3 }}>
            {general.siteTitle}
          </div>
          <div style={{ fontSize: 28, color: "#4e1a3a", marginTop: 20 }}>
            {homepage.hero.subtitle}
          </div>
        </div>
      </div>
    ),
    size,
  )
}
