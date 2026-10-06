import ThemeToggle from "./ThemeToggle"
import type { FieldKey } from "@/lib/types"

// The strip under the last card: the year, the ornament, the theme switch.
// `field` should match the card above it.
export default function Footer({ field = "cream" }: { field?: FieldKey }) {
  return (
    <footer className={`foot f-${field}`}>
      <span className="flex items-center gap-5">
        {new Date().getFullYear()}
        <a href="/admin" className="text-button">Admin</a>
      </span>
      <span className="orn" aria-hidden="true" />
      <ThemeToggle />
    </footer>
  )
}
