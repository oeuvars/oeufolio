import { useEffect, useState } from 'react'

import { MONO } from './styles'

type Note = { id: number; login: string; avatar: string; body: string; date: string; href: string }

/**
 * The guestbook, kept as GitHub issues on the owner's public profile repository: signing it opens a new issue titled
 * "Guestbook", and every issue so titled shows here, newest first. There is no server of its own.
 */
export function useGuestbook(repo: string) {
  const [notes, setNotes] = useState<Note[] | null>(null)

  useEffect(() => {
    let live = true
    fetch(`https://api.github.com/repos/${repo}/issues?state=all&per_page=100`)
      .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
      .then((issues: { id: number; title: string; body: string | null; created_at: string; html_url: string; pull_request?: unknown; user: { login: string; avatar_url: string } }[]) => {
        if (!live) return
        setNotes(
          issues
            .filter((issue) => !issue.pull_request && issue.title.trim().toLowerCase().startsWith('guestbook') && issue.body?.trim())
            .map((issue) => ({
              id: issue.id,
              login: issue.user.login,
              avatar: issue.user.avatar_url,
              body: issue.body!.trim(),
              date: new Date(issue.created_at).toLocaleDateString('en', { day: 'numeric', month: 'short', year: 'numeric' }),
              href: issue.html_url,
            })),
        )
      })
      .catch(() => live && setNotes([]))
    return () => {
      live = false
    }
  }, [repo])

  return notes
}

export const signHref = (repo: string) => `https://github.com/${repo}/issues/new?title=Guestbook&body=${encodeURIComponent('Leave your note here.')}`

export function Guestbook({ repo, notes }: { repo: string; notes: Note[] | null }) {
  if (notes && notes.length > 0) {
    return (
      <ul className="flex flex-col gap-3 pt-5 pb-2">
        {notes.map((note) => (
          <li key={note.id} className="rounded-[6px] border border-black/5 bg-zinc-50 px-4 py-3 dark:border-white/5 dark:bg-[#09090b]">
            <a href={note.href} className="flex items-center gap-2">
              <img src={note.avatar} alt="" className="size-5 rounded-full" />
              <span className="text-[13px] font-medium text-zinc-900 dark:text-zinc-100">{note.login}</span>
              <span className={`${MONO} ml-auto text-[10px] text-zinc-400 dark:text-zinc-600`}>{note.date}</span>
            </a>
            <p className="mt-2 text-[13px] leading-relaxed whitespace-pre-line text-zinc-600 dark:text-zinc-400">{note.body}</p>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className="pt-5 pb-2">
      <a
        href={signHref(repo)}
        className="group flex flex-col items-center justify-center gap-2 rounded-[6px] border border-dashed border-black/15 py-8 transition-colors hover:border-black/30 dark:border-white/10 dark:hover:border-white/25"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" className="size-4 text-zinc-400 dark:text-zinc-600" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <p className="text-[13px] text-zinc-500 dark:text-zinc-400">{notes === null ? 'Opening the guestbook' : 'No notes yet. Be the first to sign.'}</p>
      </a>
    </div>
  )
}
