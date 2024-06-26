import type { Metadata } from "next";
import "./globals.css";
import { GeistSans } from 'geist/font/sans';
import { Toaster } from "react-hot-toast";


export const metadata: Metadata = {
  title: "Anurag | Oeuvars",
  description: "Oeuvars is landing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={GeistSans.className}>
        <Toaster position="top-center" />
        {children}
      </body>
    </html>
  );
}
