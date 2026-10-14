import type { Like, Playlist } from '../../types'
import { PROP } from './classes'

type RecordSleeveProps = {
  like: Like
  /** The playlist the record stands for. Its cover is printed on the sleeve. */
  playlist: Playlist
}

/**
 * The electric guitars like: a seven-inch single in a gloss sleeve that carries the cover of the playlist
 * and opens it. The record shows at the mouth of the sleeve. The sleeve is the link.
 */
export function RecordSleeve({ like, playlist }: RecordSleeveProps) {
  return (
    <article data-prop="record" className={`${PROP} z-2 h-[15.625em] w-[20em] [--k:1.5]`}>
      <a
        href={playlist.href}
        target="_blank"
        rel="noreferrer"
        draggable={false}
        aria-label={`${like.subject}: ${playlist.title}, a playlist on Spotify`}
        className="block h-full w-[15.625em]"
      />
    </article>
  )
}
