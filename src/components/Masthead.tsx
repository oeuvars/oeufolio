/** The ink's wear, as SVG filters: one for the big word, and a lighter one that small letters survive. */
function Wear() {
  return (
    <svg aria-hidden width="0" height="0" className="absolute">
      <defs>
        {/*
         * Ink from an old block: an edge pushed about a little by the paper, fine pitting where it did not
         * take, a few places rubbed thinner, and a little bleed round all of it.
         */}
        <filter id="worn" x="-4%" y="-10%" width="108%" height="120%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="3" seed="2" result="edge" />
          <feDisplacementMap in="SourceGraphic" in2="edge" scale="2.5" xChannelSelector="R" yChannelSelector="G" result="rough" />
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="7" result="grain" />
          <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3 0 0 0 -0.45" result="taken" />
          <feComposite in="rough" in2="taken" operator="in" result="pitted" />
          <feTurbulence type="fractalNoise" baseFrequency="0.025" numOctaves="2" seed="4" result="rubbing" />
          <feColorMatrix in="rubbing" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.2 0 0 0 -0.15" result="kept" />
          <feComposite in="pitted" in2="kept" operator="in" result="ink" />
          <feGaussianBlur in="ink" stdDeviation="0.6" result="bleed" />
          <feMerge>
            <feMergeNode in="bleed" />
            <feMergeNode in="ink" />
          </feMerge>
        </filter>
        <filter id="worn-fine" x="-4%" y="-20%" width="108%" height="140%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0.08" numOctaves="2" seed="5" result="edge" />
          <feDisplacementMap in="SourceGraphic" in2="edge" scale="1.6" xChannelSelector="R" yChannelSelector="G" result="rough" />
          <feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="2" seed="9" result="grain" />
          <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3 0 0 0 -0.55" result="taken" />
          <feComposite in="rough" in2="taken" operator="in" result="ink" />
          <feGaussianBlur in="ink" stdDeviation="0.4" result="bleed" />
          <feMerge>
            <feMergeNode in="bleed" />
            <feMergeNode in="ink" />
          </feMerge>
        </filter>
      </defs>
    </svg>
  )
}

/**
 * The poster's title: yellow capitals in Geist Mono, spaced wide and centred over the picture, the first
 * words small and the last one large. It is printed from a worn block, not set (Wear).
 */
export function Masthead() {
  return (
    <header className="text-center font-geist text-[#f6cf43] uppercase">
      <Wear />
      <h1 className="font-extrabold">
        <span className="block text-[2.5cqw] leading-none tracking-[0.5em] [margin-right:-0.5em] [filter:url(#worn-fine)]">
          Where I&rsquo;ve
        </span>
        <span className="mt-[0.1em] block text-[13cqw] leading-[1.05] tracking-[0.06em] [margin-right:-0.06em] [filter:url(#worn)]">Worked</span>
      </h1>
    </header>
  )
}
