import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { type ReactNode } from "react";

const timeThemeScript = `
  (() => {
    const applyTimeTheme = () => {
      const hour = new Date().getHours();
      const theme = hour >= 6 && hour < 18 ? "light" : "dark";
      document.documentElement.dataset.timeTheme = theme;
      document.documentElement.style.colorScheme = theme;
    };

    applyTimeTheme();
    window.setInterval(applyTimeTheme, 60000);
  })();
`;

export const metadata = {
  metadataBase: new URL("https://anurag.gg"),
  title: {
    default: "Anurag Das",
    template: "%s | Anurag Das",
  },
  description:
    "Anurag Das — photographs, notes, and things in progress.",
  keywords: [
    "Anurag Das",
    "Oeuvars",
    "Personal journal",
    "Electric guitars",
    "Sports cars",
    "Arsenal",
    "Industrial design",
    "Software Engineer",
  ],
  authors: [
    {
      name: "Anurag Das",
      url: "https://anurag.gg",
    },
  ],
  creator: "Anurag Das",
  publisher: "Anurag Das",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "https://anurag.gg",
  },
  openGraph: {
    title: "Anurag Das",
    description:
      "Photographs, notes, and things in progress.",
    url: "https://anurag.gg",
    siteName: "Anurag Das",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Anurag Das",
    description:
      "Photographs, notes, and things in progress.",
    creator: "@oeuvars",
  },
} satisfies Metadata;

export default function Layout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" data-time-theme="light" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: timeThemeScript }} />
      </head>
      <body>
        <Toaster position="top-center" />
        {children}
      </body>
    </html>
  );
}
