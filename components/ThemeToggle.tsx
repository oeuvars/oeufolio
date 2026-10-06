'use client'

import { useTheme } from "@/lib/theme"

// The theme switch, named for what it does in a cinema: lights up is the light
// theme, lights down the dark one.
export default function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme()
  const up = theme !== "dark"
  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={up}
      aria-label={up ? "House lights are up. Switch to the dark theme" : "House lights are down. Switch to the light theme"}
      className={`text-button ${className ?? ""}`}
    >
      House lights
      <span className="lights" data-on={up} aria-hidden="true" />
    </button>
  )
}
