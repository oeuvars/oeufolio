import { useState } from 'react'

type CopyEmailProps = {
  email: string
}

export function CopyEmail({ email }: CopyEmailProps) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    await navigator.clipboard.writeText(email)
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }

  return (
    <button type="button" onClick={copy} className="link cursor-pointer text-left italic">
      {copied ? 'Copied' : email}
    </button>
  )
}
