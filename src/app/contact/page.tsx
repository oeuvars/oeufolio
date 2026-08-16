import type { Metadata } from "next";
import Link from "next/link";
import {
  IconArrowLeft,
  IconArrowUpRight,
  IconBrandGithub,
  IconBrandInstagram,
  IconBrandX,
} from "@tabler/icons-react";

export const metadata: Metadata = {
  title: "Contact",
  description: "The separate contact page for Anurag Das.",
};

const links = [
  {
    label: "GitHub",
    href: "https://github.com/oeuvars",
    icon: IconBrandGithub,
  },
  {
    label: "Instagram",
    href: "https://www.instagram.com/oeuvars/",
    icon: IconBrandInstagram,
  },
  {
    label: "X",
    href: "https://twitter.com/oeuvars",
    icon: IconBrandX,
  },
] as const;

export default function ContactPage() {
  return (
    <main className="contact-shell">
      <section className="contact-book" aria-labelledby="contact-title">
        <header className="contact-top">
          <Link href="/" className="back-link">
            <IconArrowLeft size={15} /> Receiver
          </Link>
          <div className="contact-line-status">
            <i aria-hidden="true" />
            <span>AD–00 / external lines</span>
          </div>
        </header>

        <div className="contact-content">
          <div className="contact-channel" aria-hidden="true">
            <span>00</span>
            <i />
          </div>
          <p className="overline">Channel 00</p>
          <h1 id="contact-title">Elsewhere.</h1>
          <p>
            Links, if you need them.
          </p>

          <div className="contact-list">
            {links.map(({ label, href, icon: Icon }) => (
              <Link href={href} target="_blank" rel="noreferrer" key={label}>
                <span><Icon size={17} /> {label}</span>
                <IconArrowUpRight size={15} />
              </Link>
            ))}
          </div>

          <div className="contact-postscript">Line open</div>
        </div>

        <footer className="contact-footer">
          <span>ANURAG DAS · OEU VARS</span>
          <div className="contact-controls" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
          </div>
          <span>KOLKATA · INDIA</span>
        </footer>
      </section>
    </main>
  );
}
