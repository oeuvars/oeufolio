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
        <p className="display absolute top-[50%] left-[4%] text-[1.4rem]">ure</p>
        <p className="label absolute top-[56%] left-[4%] border border-ink/60 px-[0.4em] py-[0.15em]">01-A</p>
        <p className="label absolute top-[64%] left-[4%] leading-[1.7] font-bold">
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
        <p className="label absolute top-[3%] left-[8%] leading-[1.7]">
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
      </div>
    )
  }

  if (index === 2) {
    return (
      <img
        aria-hidden
        src="/photos/blur.jpg"
        alt=""
        className="absolute inset-0 size-full object-cover object-[40%_50%]"
      />
    )
  }

  return (
    <div aria-hidden className="absolute inset-0 bg-[#141311]">
      <img
        src="/photos/lamp.jpg"
        alt=""
        className="absolute inset-0 size-full object-cover opacity-70"
      />
      <div className="absolute inset-[0.6rem] border border-white/25" />
      <svg viewBox="0 0 24 24" className="absolute top-[24%] left-1/2 w-[28%] -translate-x-1/2 text-white/85">
        <path
          fill="currentColor"
          d="M12 1c1 6 5 10 11 11-6 1-10 5-11 11-1-6-5-10-11-11 6-1 10-5 11-11z"
        />
      </svg>
    </div>
  )
}
