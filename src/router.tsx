import { createRouter as createTanStackRouter } from '@tanstack/react-router'
import { ErrorPage } from './components/error-page'
import { routeTree } from './route-tree.gen'

export const getRouter = () => {
  const router = createTanStackRouter({
    routeTree,
    scrollRestoration: true,
    defaultPreload: 'intent',
    defaultPreloadStaleTime: 0,
    // A page that breaks shows the error page, wherever in the tree it broke.
    defaultErrorComponent: ErrorPage,
  })

  return router
}

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof getRouter>
  }
  interface StaticDataRouteOption {
    /** The page is shown on its own, outside the stack of folders. */
    bare?: boolean
  }
}
