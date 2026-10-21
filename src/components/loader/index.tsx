import crows from './crows.txt?raw'
import script from './ascii.js?raw'

/**
 * The paper laid over the site while its pictures come in (ascii.js), with the crows it plays (crows.txt) in an inert
 * block beside it. Its script runs where it stands, at the top of the body, before the bundle loads, and fills the
 * empty box above it; React leaves the box's inside alone. The scene that came before it is kept in sketch.js.
 */
export const Loader = () => (
  <>
    <div id="loader" suppressHydrationWarning dangerouslySetInnerHTML={{ __html: '' }} />
    <script type="text/plain" id="loader-crows" dangerouslySetInnerHTML={{ __html: crows }} />
    <script dangerouslySetInnerHTML={{ __html: script }} />
  </>
)
