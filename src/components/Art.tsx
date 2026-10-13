const pixels = [
  [8, 6], [12, 6], [8, 10], [16, 10], [12, 14], [20, 14], [4, 18], [16, 18], [24, 18],
  [8, 22], [12, 26], [20, 26], [4, 30], [16, 30], [10, 34], [22, 34],
]

type ArtProps = {
  index: number
}

/** Cropped decorative fragments shown on a collapsed sheet. */
export function Art({ index }: ArtProps) {
  if (index === 0) {
    return (
      <div aria-hidden className="absolute inset-0 border-t border-ink/60">
        <div className="absolute top-[5%] left-0 h-[1.4%] w-[34%] bg-ink" />
        <div
          className="absolute top-[24%] left-[8%] h-[5%] w-[70%]"
          style={{
            backgroundImage:
              'repeating-linear-gradient(90deg, var(--ink) 0 2px, transparent 2px 4px, var(--ink) 4px 5px, transparent 5px 9px, var(--ink) 9px 12px, transparent 12px 14px)',
          }}
        />
        <div className="absolute top-[33%] left-0 h-[14%] w-[26%] bg-ink" />
        <div className="absolute top-[42%] left-0 h-[5%] w-[64%] bg-ink" />
        <p className="display absolute top-[49.5%] left-[4%] text-[1.4rem]">ure</p>
        <p className="mono absolute top-[56%] left-[4%] border border-ink/60 px-[0.4em] py-[0.15em]">01-A</p>
        <p className="mono absolute top-[63%] left-[4%] leading-[1.7] font-bold">
          walking,
          <br />
          way,
          <br />
          still.
        </p>
      </div>
    )
  }

  if (index === 1) {
    return (
      <div aria-hidden className="absolute inset-0">
        <p className="mono absolute top-[3%] left-[8%] leading-[1.7]">
          log
          <br />
          00:47
          <br />
          red
        </p>
        {pixels.map(([x, y]) => (
          <span
            key={`${x}-${y}`}
            className="absolute size-[0.55rem] bg-ink"
            style={{ left: `${x * 3}%`, top: `${6 + y * 1.4}%` }}
          />
        ))}
        <img
          src="/photos/mountain.jpg"
          alt=""
          className="absolute top-[56%] left-[8%] h-[14%] w-[62%] border border-ink/60 object-cover object-right grayscale"
        />
        <p className="mono absolute top-[73%] left-[8%] leading-[1.7] font-bold">
          s open
          <br />
          spoke
        </p>
        <p className="mono absolute bottom-[3%] left-[8%] leading-[1.7] font-bold">
          void
          <br />
          replies
        </p>
      </div>
    )
  }

  if (index === 2) {
    return (
      <img
        aria-hidden
        src="/photos/blur.jpg"
        alt=""
        className="absolute inset-0 size-full object-cover object-[40%_50%] [filter:sepia(0.45)_saturate(0.8)_brightness(0.7)_contrast(1.15)]"
      />
    )
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
