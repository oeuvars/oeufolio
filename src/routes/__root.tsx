import { HeadContent, Outlet, Scripts, createRootRoute } from '@tanstack/react-router'

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
        href: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' fill='%23272521'/%3E%3Crect x='8' y='8' width='9' height='24' fill='%23ece4cc'/%3E%3Crect x='19' y='12' width='13' height='20' fill='%237d8798'/%3E%3C/svg%3E",
      },
      {
        rel: 'stylesheet',
        href: appCss,
      },
    ],
  }),
  shellComponent: RootDocument,
  component: RootLayout,
})

function RootLayout() {
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
