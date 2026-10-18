import { HeadContent, Outlet, Scripts, createRootRoute, useRouterState } from '@tanstack/react-router'

import { NotFound } from '../components/NotFound'
import { SiteShell } from '../components/SiteShell'

import appCss from '../styles.css?url'

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
      {
        title: 'oeuvars | Portfolio',
      },
      {
        name: 'description',
        content: 'Portfolio of oeuvars, laid out as a stack of file folders.',
      },
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
})

function RootLayout() {
  // A path that is not a page has no strip to open, so it is shown on its own, outside the stack.
  const lost = useRouterState({ select: (state) => state.matches.some((match) => match._notFound) })
  if (lost) return <Outlet />

  return (
    <SiteShell>
      <Outlet />
    </SiteShell>
  )
}

function RootDocument({ children }: { children: React.ReactNode }) {
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
