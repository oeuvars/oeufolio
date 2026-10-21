import birds from './birds.txt?raw'
import script from './tetons.js?raw'

/**
 * The picture laid over the site while its pictures come in (tetons.js), with the birds it flies (birds.txt) in an
 * inert block beside it. Its script runs where it stands, at the top of the body, before the bundle loads, and fills
 * the empty box above it; React leaves the box's inside alone. The loaders that came before it are kept in crows.js
 * and sketch.js.
 */
export const Loader = () => (
  <>
    <div id="loader" suppressHydrationWarning dangerouslySetInnerHTML={{ __html: '' }} />
    <script type="text/plain" id="loader-birds" dangerouslySetInnerHTML={{ __html: birds }} />
    <script dangerouslySetInnerHTML={{ __html: script }} />
  </>
)
