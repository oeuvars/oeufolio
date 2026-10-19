import { HeadContent, Outlet, Scripts, createRootRoute, useRouterState } from '@tanstack/react-router'

import { ErrorPage, InStack } from '../components/error-page'
import { NotFound } from '../components/not-found'
import { SiteShell } from '../components/site-shell'
import { pages, site } from '../content'

import appCss from '../styles.css?url'

const RootLayout = () => {
  // A path that is not a page, a page that broke, and a page that is not one of the folders (the résumé) have no
  // strip to open, so each is shown on its own, outside the stack.
  const bare = useRouterState({
    select: (state) => state.matches.some((match) => match._notFound || match.status === 'error' || match.staticData.bare),
  })
  if (bare) return <Outlet />

  return (
    <InStack.Provider value>
      <SiteShell>
        <Outlet />
      </SiteShell>
    </InStack.Provider>
  )
}

const RootDocument = ({ children }: { children: React.ReactNode }) => {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}

        <Scripts />
      </body>
    </html>
  )
}

export const Route = createRootRoute({
  head: () => ({
    meta: [
      {
        charSet: 'utf-8',
      },
      {
        name: 'viewport',
        content: 'width=device-width, initial-scale=1',
      },
      // What a page without a head of its own (the 404) is called. Every page sets its own.
      {
        title: site.name,
      },
      {
        name: 'description',
        content: pages.basics.description,
      },
      { name: 'author', content: site.name },
      { property: 'og:site_name', content: site.name },
      { property: 'og:locale', content: site.locale },
      { name: 'twitter:site', content: site.x },
      { name: 'twitter:creator', content: site.x },
    ],
    links: [
      {
        rel: 'icon',
        href: '/favicon.ico',
        sizes: 'any',
      },
      {
        rel: 'apple-touch-icon',
        href: '/apple-touch-icon.png',
      },
      {
        rel: 'manifest',
        href: '/site.webmanifest',
      },
      {
        rel: 'stylesheet',
        href: appCss,
      },
    ],
  }),
  shellComponent: RootDocument,
  component: RootLayout,
  notFoundComponent: NotFound,
  errorComponent: ErrorPage,
})
