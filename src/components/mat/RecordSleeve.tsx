import type { Like, Playlist } from '../../types'
import { PROP, RENDER, SKIN } from './classes'

type RecordSleeveProps = {
  like: Like
  /** The playlist the record stands for. Its cover is printed on the sleeve. */
  playlist: Playlist
}

/**
 * The electric guitars like: a seven-inch single in a gloss sleeve that carries the cover of the playlist
 * and opens it. The record shows at the mouth of the sleeve and stays there.
 */
export function RecordSleeve({ like, playlist }: RecordSleeveProps) {
  return (
    <article data-prop="record" className={`${PROP} z-2 h-[15.625em] w-[20em] [--k:1.5] [--tall:0.12] stacked:[--k:1.2]`}>
      <div aria-hidden className={`${RENDER} absolute top-[0.5625em] right-0 aspect-square w-[14.5em] bg-[url(/objects/mat/disc.avif)]`}>
        <i className={`${RENDER} absolute inset-[31.03%] bg-[url(/objects/mat/label.avif)]`} />
      </div>
      <a
        href={playlist.href}
        target="_blank"
        rel="noreferrer"
        draggable={false}
        aria-label={`${like.subject}: ${playlist.title}, a playlist on Spotify`}
        className="relative isolate block h-full w-[15.625em] [--bleed:0.8]"
      >
        <i aria-hidden className={`${SKIN} bg-[url(/objects/mat/sleeve.avif)]`} />
      </a>
    </article>
  )
}
