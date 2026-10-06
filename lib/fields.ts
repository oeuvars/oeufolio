import type { FieldKey } from "@/lib/types"

const FIELD_KEYS: readonly FieldKey[] = [
  "pink",
  "marigold",
  "turquoise",
  "red",
  "mint",
  "cream",
  "teal",
]

// The order parts take a field in when their gallery entry names none.
const PART_ROTATION: readonly FieldKey[] = ["marigold", "turquoise", "red", "mint", "pink"]

export function isFieldKey(value: unknown): value is FieldKey {
  return typeof value === "string" && (FIELD_KEYS as readonly string[]).includes(value)
}

export function partField(field: FieldKey | undefined, index: number): FieldKey {
  return field ?? PART_ROTATION[index % PART_ROTATION.length]
}
