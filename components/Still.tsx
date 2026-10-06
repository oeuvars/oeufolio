import Image from "next/image"

interface StillProps {
  // Path under public/, e.g. /assets/galleries/stills/01_after-six.jpg
  src: string
  alt: string
  // The note, set as a subtitle at the bottom of the frame.
  note?: string
  // CSS object-position for the crop.
  focus?: string
  sizes: string
  // Above the fold: fetch ahead of the lazy queue.
  eager?: boolean
  blurDataURL?: string
  className?: string
}

// A still in its window: the fixed-ratio frame with a keyline, and the note
// burned in as a subtitle.
export default function Still({ src, alt, note, focus, sizes, eager = false, blurDataURL, className }: StillProps) {
  return (
    <figure className={className ? `frame ${className}` : "frame"}>
      <Image
        src={src}
        alt={alt}
        fill
        sizes={sizes}
        style={focus ? { objectPosition: focus } : undefined}
        {...(eager && { loading: "eager" as const, fetchPriority: "high" as const })}
        {...(blurDataURL && { placeholder: "blur" as const, blurDataURL })}
      />
      {note && <figcaption className="sub">{note}</figcaption>}
    </figure>
  )
}
