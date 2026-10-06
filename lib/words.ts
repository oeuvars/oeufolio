const SMALL_NUMBERS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]

// 5 → "five". Counts past ten stay as digits.
export function countWord(count: number): string {
  return SMALL_NUMBERS[count] ?? String(count)
}
