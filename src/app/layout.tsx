import type { Metadata } from "next";
import "./globals.css";
import { Plus_Jakarta_Sans } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { type ReactNode } from "react";
import { Stack } from "@/components/stack";

const plusJakartaSans = Plus_Jakarta_Sans({ subsets: ["latin"] });

export const metadata = {
  metadataBase: new URL("https://anurag.gg"),
  title: {
    default: "Anurag | Oeuvars",
    template: "%s | Anurag Das",
  },
  description:
    "Anurag Das - Software Engineer building servers and interfaces at Cybership",
  keywords: [
    "Anurag Das",
    "Oeuvars",
    "Software Engineer",
    "Full Stack Enginner",
    "Cybership",
    "Engineer",
    "Portfolio",
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
    title: "Anurag | Oeuvars",
    description:
      "Software Engineer building servers and interfaces at Cybership",
    url: "https://anurag.gg",
    siteName: "Anurag Das",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Anurag | Oeuvars",
    description:
      "Software Engineer building servers and interfaces at Cybership",
    creator: "@oeuvars",
  },
} satisfies Metadata;

export default function Layout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <Stack as="body" className={plusJakartaSans.className}>
        <Toaster position="top-center" />
        {children}
      </Stack>
    </html>
  );
}
