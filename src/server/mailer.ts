import { profile } from '../content'
import { isEmail } from '../lib/utils'
import type { ChatNote, ChatReceipt } from '../types'

const LONGEST = 4000
// How many notes one address may send in a window, so a script cannot fill the inbox.
const LIMIT = { notes: 5, window: 10 * 60 * 1000 }

/**
 * Hands a reader's note from the résumé to my inbox through Resend's API. RESEND_API_KEY must be set on the server,
 * and MAIL_FROM, when set, must be an address on a domain Resend has verified. The reader's address goes in Reply-To,
 * so answering the email answers them.
 */
export class Mailer {
  private sent = new Map<string, number[]>()

  /** Checks a note's shape, since it arrives from the open web. */
  read = (input: unknown): ChatNote => {
    const note = (input ?? {}) as Partial<Record<keyof ChatNote, unknown>>
    const text = (value: unknown) => (typeof value === 'string' ? value.trim() : '')
    return { message: text(note.message).slice(0, LONGEST), email: text(note.email), website: text(note.website) }
  }

  send = async (note: ChatNote, from: string): Promise<ChatReceipt> => {
    // A bot that filled the hidden field is told it worked and sends nothing.
    if (note.website) return { ok: true }
    if (!note.message || !isEmail(note.email)) return { ok: false, reason: 'invalid' }
    if (!this.admit(from)) return { ok: false, reason: 'busy' }

    const key = process.env.RESEND_API_KEY
    if (!key) return { ok: false, reason: 'unconfigured' }

    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: process.env.MAIL_FROM ?? 'Résumé <resume@anurag.gg>',
        to: [profile.email],
        reply_to: note.email,
        subject: `A text from ${note.email}`,
        text: `${note.message}\n\n${note.email}, from the résumé's thread`,
      }),
    }).catch(() => null)

    return response?.ok ? { ok: true } : { ok: false, reason: 'failed' }
  }

  /** Counts this note against its sender's window, and says whether it may go. */
  private admit = (from: string) => {
    const now = Date.now()
    const recent = (this.sent.get(from) ?? []).filter((at) => now - at < LIMIT.window)
    if (recent.length >= LIMIT.notes) return false
    this.sent.set(from, [...recent, now])
    return true
  }
}

export const mailer = new Mailer()
