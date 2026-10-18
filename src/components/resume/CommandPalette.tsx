import { useEffect, useMemo, useRef, useState, type KeyboardEvent as KeyEvent, type ReactNode } from 'react'

import { FOCUS, MONO } from './styles'

type Command = { group: string; label: string; hint?: string; run: () => void }

/**
 * The ⌘K menu: every section, link and setting on the page, found by typing and run with Enter. ⌘K or Ctrl+K opens
 * it from anywhere on the page, Escape or a click outside closes it, and the arrow keys move through what matches.
 */
export function CommandPalette({ commands, trigger }: { commands: Command[]; trigger: (open: () => void) => ReactNode }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const input = useRef<HTMLInputElement>(null)
  const opener = useRef<Element | null>(null)

  const matches = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean)
    return commands.filter((command) => words.every((word) => `${command.group} ${command.label} ${command.hint ?? ''}`.toLowerCase().includes(word)))
  }, [commands, query])

  const show = () => {
    opener.current = document.activeElement
    setQuery('')
    setActive(0)
    setOpen(true)
  }

  const close = () => {
    setOpen(false)
    if (opener.current instanceof HTMLElement) opener.current.focus()
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        if (open) close()
        else show()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  useEffect(() => {
    if (open) input.current?.focus()
  }, [open])

  const run = (command: Command | undefined) => {
    if (!command) return
    setOpen(false)
    command.run()
  }

  const onKeyDown = (event: KeyEvent) => {
    if (event.key === 'Escape') {
      event.preventDefault()
      close()
    } else if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((index) => (matches.length ? (index + 1) % matches.length : 0))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((index) => (matches.length ? (index - 1 + matches.length) % matches.length : 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      run(matches[active])
    }
  }

  const groups = [...new Set(matches.map((command) => command.group))]

  return (
    <>
      {trigger(show)}
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 px-4 pt-[18vh] backdrop-blur-[2px]" onMouseDown={close}>
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Command menu"
            onMouseDown={(event) => event.stopPropagation()}
            onKeyDown={onKeyDown}
            className="w-full max-w-[520px] overflow-hidden rounded-xl border border-(--line) bg-(--page) shadow-[0_24px_48px_-12px_rgb(0_0_0/0.35)]"
          >
            <input
              ref={input}
              value={query}
              onChange={(event) => {
                setQuery(event.target.value)
                setActive(0)
              }}
              placeholder="Type a command or search"
              aria-label="Search commands"
              aria-controls="command-list"
              aria-activedescendant={matches[active] ? `command-${active}` : undefined}
              className="w-full border-b border-(--line) bg-transparent px-4 py-3.5 text-[14px] text-(--ink) outline-none placeholder:text-(--faint)"
            />
            <ul id="command-list" role="listbox" aria-label="Commands" className="max-h-[50vh] overflow-y-auto p-2">
              {matches.length === 0 && <li className="px-3 py-6 text-center text-[13px] text-(--muted)">Nothing matches “{query}”.</li>}
              {groups.map((group) => (
                <li key={group} role="presentation">
                  <p className={`${MONO} px-3 pt-2 pb-1 text-[10px] tracking-wider text-(--faint) uppercase`}>{group}</p>
                  <ul role="presentation">
                    {matches
                      .filter((command) => command.group === group)
                      .map((command) => {
                        const index = matches.indexOf(command)
                        return (
                          <li
                            key={command.label}
                            id={`command-${index}`}
                            role="option"
                            aria-selected={index === active}
                            onMouseMove={() => setActive(index)}
                            onClick={() => run(command)}
                            className={`flex cursor-pointer items-center justify-between rounded-md px-3 py-2 text-[13px] ${index === active ? 'bg-(--hover) text-(--ink)' : 'text-(--body)'}`}
                          >
                            {command.label}
                            {command.hint && <span className="text-[12px] text-(--faint)">{command.hint}</span>}
                          </li>
                        )
                      })}
                  </ul>
                </li>
              ))}
            </ul>
            <p className={`${MONO} flex gap-4 border-t border-(--line) px-4 py-2 text-[10px] tracking-wider text-(--faint) uppercase`}>
              <span>↑↓ to move</span>
              <span>Enter to open</span>
              <span>Esc to close</span>
            </p>
          </div>
        </div>
      )}
    </>
  )
}

/** The ⌘K key the header shows, opening the menu when pressed. */
export function PaletteKey({ onOpen }: { onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label="Open the command menu"
      className={`flex h-7 items-center gap-1 rounded-md border border-(--line) bg-(--page) px-2 text-[11px] font-medium text-(--muted) shadow-[0_1px_2px_rgb(0_0_0/0.06)] transition-colors hover:text-(--ink) ${FOCUS}`}
    >
      <span className="text-[10px]">⌘</span>K
    </button>
  )
}
