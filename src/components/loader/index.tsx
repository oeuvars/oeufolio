import script from './tetons.js?raw'

/**
 * The picture laid over the site while its pictures come in (tetons.js). Its script runs where it stands, at the top
 * of the body, before the bundle loads, and fills the empty box above it; React leaves the box's inside alone. The
 * loaders that came before it are kept in crows.js and sketch.js.
 */
export const Loader = () => (
  <>
    <div id="loader" suppressHydrationWarning dangerouslySetInnerHTML={{ __html: '' }} />
    <script dangerouslySetInnerHTML={{ __html: script }} />
  </>
)
