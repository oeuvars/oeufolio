// Class lists the objects share. Each object adds its own size, layer and material on top.

// Any object on the mat: placed by Mat, scaled whole by its font size, and throwing a shadow.
// --k is its true size beside the others, --tall how high it stands, --bleed how far its render overhangs it.
export const PROP = [
  'placed cast-shadow absolute top-0 left-0 text-[length:calc(16px*var(--s)*var(--k,1))] opacity-0 touch-pan-y',
  'pointer-fine:cursor-grab pointer-fine:touch-none pointer-fine:data-[held=true]:cursor-grabbing',
  'data-[held=true]:scale-[1.035] data-[held=true]:[--lift:2.6]',
  'group-data-[ready=true]/mat:settling group-data-[ready=true]/mat:opacity-100',
  'group-data-[ready=true]/mat:data-[held=true]:gripped',
].join(' ')

// A render from the studio, stretched over its box.
export const RENDER = 'bg-size-[100%_100%] bg-center bg-no-repeat'

// The render behind an object. It carries the material, the outline, the relief, the type and the soft shadow
// where the object meets the mat, and overhangs the box by --bleed em on every side.
export const SKIN = `${RENDER} pointer-events-none absolute -inset-[calc(var(--bleed,0)*1em)] -z-1`

// Type the render already has. The words stay in the page for readers, unpainted.
export const BAKED = 'text-transparent'

// The one thing that cannot be baked: the clock.
export const LIVE = 'opacity-80 mix-blend-multiply'

export const KICKER = 'font-sans text-[0.52em]/[1.3] font-bold tracking-[0.22em] uppercase'
