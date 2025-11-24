import type { Metadata } from "next";
import "./globals.css";
import { Plus_Jakarta_Sans } from 'next/font/google';
import { Toaster } from "@/components/ui/sonner";
import { type ReactNode } from "react";
import { Stack } from "@/components/stack";

const plusJakartaSans = Plus_Jakarta_Sans({ subsets: ['latin'] });

export const metadata = {
  title: "Anurag | Oeuvars",
  description: "Anurag, etc. etc. etc.",
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
