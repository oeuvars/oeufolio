'use client'

import { useEffect, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import PlayButton from "./PlayButton"
import Screening from "./Screening"
import { isFieldKey } from "@/lib/fields"
import type { FieldKey, ScreeningPart } from "@/lib/types"

export type NavLink = { href: string; label: string }

interface NavClientProps {
  // Links already filtered and ordered on the server (components/Nav.tsx)
  links: NavLink[]
  brand: string
  parts: ScreeningPart[]
  initialField: FieldKey
}

export default function NavClient({ links, brand, parts, initialField }: NavClientProps) {
  const [field, setField] = useState<FieldKey>(initialField)
  // true while the card under the bar already carries the name as its title
  const [named, setNamed] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const pathname = usePathname()
  const isHome = pathname === "/"

  // The bar takes the field of whichever card sits under it. The switch
  // happens as a card's top edge passes the bar's bottom edge, so the two
  // never overlap in different colours.
  useEffect(() => {
    let frame = 0
    const read = () => {
      frame = 0
      const bar = document.getElementById("site-bar")
      const line = bar ? bar.getBoundingClientRect().bottom : 0
      let current: Element | null = null
      for (const card of document.querySelectorAll("[data-field]")) {
        const rect = card.getBoundingClientRect()
        if (rect.top <= line && rect.bottom > line) current = card
      }
      const key = current?.getAttribute("data-field")
      if (isFieldKey(key)) setField(key)
      setNamed(current?.hasAttribute("data-named") ?? false)
    }
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(read)
    }
    read()
    window.addEventListener("scroll", onScroll, { passive: true })
    window.addEventListener("resize", onScroll)
    return () => {
      if (frame) cancelAnimationFrame(frame)
      window.removeEventListener("scroll", onScroll)
      window.removeEventListener("resize", onScroll)
    }
  }, [pathname])

  // Lock scroll while the phone menu is open; Escape closes it.
  useEffect(() => {
    if (!menuOpen) return
    const prev = document.body.style.overflow
    document.body.style.overflow = "hidden"
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => {
      document.body.style.overflow = prev
      window.removeEventListener("keydown", onKey)
    }
  }, [menuOpen])

  const resolveHref = (link: NavLink) =>
    link.href.startsWith("#") && !isHome ? `/${link.href}` : link.href

  // Two groups either side of the name, the left one taking the odd link.
  const split = Math.ceil(links.length / 2)
  const left = links.slice(0, split)
  const right = links.slice(split)

  const renderLink = (link: NavLink) => (
    <Link
      key={link.href}
      href={resolveHref(link)}
      className="bar-link"
      aria-current={pathname === link.href ? "page" : undefined}
    >
      {link.label}
    </Link>
  )

  return (
    <>
      <header id="site-bar" className={`site-bar f-${field}`}>
        <nav className="site-bar-group" aria-label="Sections">
          <div className="contents max-sm:hidden">{left.map(renderLink)}</div>
          <button
            type="button"
            className="bar-link sm:hidden"
            aria-expanded={menuOpen}
            aria-controls="site-menu"
            onClick={() => setMenuOpen(true)}
          >
            Menu
          </button>
        </nav>

        {/* The name, unless the card under the bar already says it. Phones keep the ornament. */}
        <Link href="/" className="bar-link" aria-label={`${brand}, home`}>
          <span className={named ? "orn" : "orn sm:hidden"} aria-hidden="true" />
          {!named && <span className="bar-mark max-sm:hidden">{brand}</span>}
        </Link>

        <div className="site-bar-group">
          <div className="contents max-sm:hidden">{right.map(renderLink)}</div>
          {parts.length > 0 && <PlayButton />}
        </div>
      </header>

      {menuOpen && (
        <div id="site-menu" className={`menu-card f-${field}`} role="dialog" aria-modal="true" aria-label="Menu">
          <span className="keyline" aria-hidden="true" />
          <ul className="flex flex-col items-center gap-6">
            <li>
              <Link href="/" className="menu-link" onClick={() => setMenuOpen(false)}>
                Opening
              </Link>
            </li>
            {links.map((link) => (
              <li key={link.href}>
                <Link href={resolveHref(link)} className="menu-link" onClick={() => setMenuOpen(false)}>
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
          <button type="button" className="text-button" onClick={() => setMenuOpen(false)} autoFocus>
            Close
          </button>
        </div>
      )}

      <Screening parts={parts} endTitle={brand} />
    </>
  )
}
