import { HeadContent, Scripts, createRootRoute } from '@tanstack/react-router'

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
        content: 'Portfolio of oeuvars, set as an old book.',
      },
    ],
    links: [
      {
        rel: 'icon',
        href: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='6' fill='%233a1a10'/%3E%3Cpath d='M20 6 C22 13 28 16 34 20 C28 24 22 27 20 34 C18 27 12 24 6 20 C12 16 18 13 20 6Z' fill='%23a67c1b'/%3E%3C/svg%3E",
      },
      {
        rel: 'stylesheet',
        href: appCss,
      },
    ],
  }),
  shellComponent: RootDocument,
})

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
