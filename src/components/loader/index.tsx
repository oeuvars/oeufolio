import sketch from './sketch.js?raw'

/**
 * The paper laid over the site while its pictures come in (sketch.js). Its script runs where it stands, at the top of
 * the body, before the bundle loads, and fills the empty box above it; React leaves the box's inside alone.
 */
export const Loader = () => (
  <>
    <div id="loader" suppressHydrationWarning dangerouslySetInnerHTML={{ __html: '' }} />
    <script dangerouslySetInnerHTML={{ __html: sketch }} />
  </>
)
