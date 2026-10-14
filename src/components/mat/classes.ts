// Class lists the objects share. Each object adds its own size and layer on top.

// Any object on the mat: placed by Mat over where the plate has it, and scaled whole by its font size.
// --k is its true size beside the others. What shows of it is in the plate. The box carries what the plate
// cannot: links, the parts that move, and the words for readers.
export const PROP = 'placed absolute top-0 left-0 text-[length:calc(16px*var(--s)*var(--k,1))]'

// A render from the studio, stretched over its box.
export const RENDER = 'bg-size-[100%_100%] bg-center bg-no-repeat'

// Type the render already has. The words stay in the page for readers, unpainted.
export const BAKED = 'text-transparent'
