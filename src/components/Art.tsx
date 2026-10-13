type ArtProps = {
  index: number
}

/** Cropped decorative fragments shown on a folded strip. The first page has none: it shows its badge. */
export function Art({ index }: ArtProps) {
  if (index === 1) {
    // The letter's own drawings, date and signature, down the edge of its sheet (studio/letter.py).
    return (
      <img
        aria-hidden
        src="/objects/letter-strip.avif"
        alt=""
        className="absolute inset-x-0 top-[1.5%] h-[97%] w-full object-contain"
      />
    )
  }

  // The work page's building (studio/dollhouse.py), down its right-hand side: the lift, the end of the
  // banking hall and the stairs, with the far ends of their signs.
  if (index === 2) {
    return <img aria-hidden src="/objects/dollhouse.webp" alt="" className="absolute inset-0 size-full object-cover object-[84%_50%]" />
  }

  return (
    <div aria-hidden className="absolute inset-0 bg-[linear-gradient(180deg,#1b1a19,#0d0d0d)]">
      <div className="absolute top-[3%] right-[10%] left-[34%] h-[28%] border border-white/35" />
      <svg viewBox="0 0 24 24" className="absolute top-[5%] left-[8%] w-[22%] text-white/80">
        <path
          fill="none"
          stroke="currentColor"
          strokeWidth="1.1"
          strokeLinecap="round"
          d="M12 12c0-3 3-3 3 0s-3 5-6 3-1-8 4-8 9 7 4 11"
        />
      </svg>
      <p className="absolute top-[40%] left-[2%] font-serif text-[clamp(3rem,6vw,5.5rem)] leading-none font-black text-[#d9d2bc] italic">
        al
      </p>
      <svg viewBox="0 0 24 24" className="absolute top-[53%] left-[56%] w-[26%] text-[#d9d2bc]">
        <path
          fill="currentColor"
          d="M12 1c1 6 5 10 11 11-6 1-10 5-11 11-1-6-5-10-11-11 6-1 10-5 11-11z"
        />
      </svg>
      <div className="absolute top-[34%] bottom-[3%] left-[62%] w-px bg-white/25" />
    </div>
  )
}
