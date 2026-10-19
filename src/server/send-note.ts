import { createServerFn } from '@tanstack/react-start'
import { getRequestIP } from '@tanstack/react-start/server'

import { mailer } from './mailer'

/** The résumé composer's way to my inbox: the note runs on the server, where the mail key is. */
export const sendNote = createServerFn({ method: 'POST' })
  .validator(mailer.read)
  .handler(({ data }) => mailer.send(data, getRequestIP({ xForwardedFor: true }) ?? 'unknown'))
