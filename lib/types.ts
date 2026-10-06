// Contracts shared across lib/ and components/. A type used outside the file
// that needs it is declared here, not in an implementation file.

// A field is a flat ground colour paired with the one ink allowed on it.
// The values are the suffixes of the `.f-*` classes in app/globals.css.
export type FieldKey =
  | "pink"
  | "marigold"
  | "turquoise"
  | "red"
  | "mint"
  | "cream"
  | "teal"

// One part of the picture as the screening needs it: a still, its title card
// and its subtitle.
export interface ScreeningPart {
  title: string
  note?: string
  src: string
  alt: string
  field: FieldKey
  focus?: string
}

// The outbound links the credits card knows how to label.
export type SocialKey = "github" | "instagram" | "x" | "facebook" | "website"
