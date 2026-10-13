import { useState } from 'react'

import { cn } from '../lib/utils'

type CopyEmailProps = {
  email: string
  className?: string
}

export function CopyEmail({ email, className }: CopyEmailProps) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    await navigator.clipboard.writeText(email)
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }

  return (
    <button type="button" onClick={copy} className={cn('label link cursor-pointer text-left', className)}>
      {copied ? 'Copied' : email}
    </button>
  )
}
