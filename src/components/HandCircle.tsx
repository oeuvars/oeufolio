type HandCircleProps = {
  children: React.ReactNode
}

export function HandCircle({ children }: HandCircleProps) {
  return (
    <span className="relative inline-block">
      {children}
      <svg
        aria-hidden
        viewBox="0 0 220 80"
        preserveAspectRatio="none"
        className="pointer-events-none absolute top-1/2 left-1/2 h-[126%] w-[116%] -translate-x-1/2 -translate-y-1/2 overflow-visible"
      >
        <path
          className="hand-circle"
          pathLength={1}
          d="M16 46 C6 20 62 7 114 9 C170 11 216 22 211 46 C206 68 152 75 104 72 C58 70 14 64 9 36 C8 27 15 21 27 17"
          fill="none"
          stroke="var(--color-rubric)"
          strokeWidth={2.4}
          strokeLinecap="round"
        />
      </svg>
    </span>
  )
}
