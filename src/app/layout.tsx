import type { Metadata } from "next";
import "./globals.css";
import { Plus_Jakarta_Sans } from 'next/font/google';
import { Toaster } from "@/components/ui/sonner";
import { type ReactNode } from "react";

const plusJakartaSans = Plus_Jakarta_Sans({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: "Anurag | Oeuvars",
  description: "Anurag, etc. etc. etc.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={plusJakartaSans.className}>
        <Toaster position="top-center" />
        {children}
      </body>
    </html>
  );
}
