import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import { Plus_Jakarta_Sans } from 'next/font/google';

const plusJakartaSans = Plus_Jakarta_Sans({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: "Anurag | Oeuvars",
  description: "Anurag, etc. etc. etc.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
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
