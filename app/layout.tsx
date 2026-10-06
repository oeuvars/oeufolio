import type { Metadata } from "next"
import { Jost } from "next/font/google"
import { SpeedInsights } from "@vercel/speed-insights/next"
import { Analytics } from "@vercel/analytics/next"
import { ThemeProvider } from "@/lib/theme"
import { SITE_URL } from "@/lib/site"
import { getHeroImages } from "@/lib/data"
import { JsonLd } from "@/components/JsonLd"
import { buildPersonSchema } from "@/lib/jsonld"
import content from "@/data/general.json"
import "./globals.css"

// The one family on the site: the open-licence face closest to Futura.
const jost = Jost({
  variable: "--font-jost",
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
})

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: content.siteTitle,
  description: content.description,
  manifest: "/site.webmanifest",
  openGraph: {
    title: content.siteTitle,
    description: content.description,
    // No static images: the opengraph-image.tsx file convention generates them.
    locale: "en_US",
    type: "website",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const hero = getHeroImages()
  const personImage = hero.desktop[0] ? `${SITE_URL}/assets/${hero.desktop[0]}` : undefined

  return (
    <html lang="en" className={jost.variable} suppressHydrationWarning>
      <body>
        <JsonLd data={buildPersonSchema(personImage)} />
        <ThemeProvider defaultTheme={content.defaultTheme as 'light' | 'dark'}>
          {children}
        </ThemeProvider>
        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  )
}
