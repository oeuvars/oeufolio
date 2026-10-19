import { useEffect, useMemo, useRef, useState, type KeyboardEvent as KeyEvent, type ReactNode } from 'react'

import { MONO } from './styles'

type Command = { group: string; label: string; icon: ReactNode; key?: string; run: () => void }

const editable = (target: EventTarget | null) =>
  target instanceof HTMLElement && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))

const Glyph = ({ children, className = 'size-4' }: { children: ReactNode; className?: string }) => {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className={`${className} shrink-0`} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {children}
    </svg>
  )
}

/**
 * The ⌘K menu, after the reference's: every section, link and setting on the page, found by typing and run with
 * Enter. ⌘K or Ctrl+K opens it, Escape or a click outside closes it, the arrow keys move through what matches, and
 * Shift with a command's letter runs it from anywhere on the page.
 */
export const CommandPalette = ({ commands, trigger }: { commands: Command[]; trigger: (open: () => void) => ReactNode }) => {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const input = useRef<HTMLInputElement>(null)
  const opener = useRef<Element | null>(null)

  const matches = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean)
    return commands.filter((command) => words.every((word) => `${command.group} ${command.label}`.toLowerCase().includes(word)))
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

  const run = (command: Command | undefined) => {
    if (!command) return
    setOpen(false)
    command.run()
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        if (open) close()
        else show()
        return
      }
      if (!event.shiftKey || event.metaKey || event.ctrlKey || event.altKey || editable(event.target)) return
      const command = commands.find((c) => c.key && c.key === event.key.toUpperCase())
      if (command) {
        event.preventDefault()
        run(command)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  useEffect(() => {
    if (open) input.current?.focus()
  }, [open])

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
        <>
          <div aria-hidden="true" className="fixed inset-0 z-50 bg-black/50" onMouseDown={close} />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="palette-title"
            onKeyDown={onKeyDown}
            className="fixed top-1/2 left-1/2 z-50 grid w-full max-w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-xl border border-neutral-100 bg-white p-0 shadow-lg sm:max-w-lg dark:border-neutral-900 dark:bg-[#0a0a0a]"
          >
            <div className="flex h-full w-full flex-col overflow-hidden rounded-md bg-white text-zinc-900 dark:bg-[#0a0a0a] dark:text-zinc-50">
              <div className="flex items-center gap-4 border-b border-zinc-100 p-4 dark:border-zinc-800">
                <div className="flex size-10 items-center justify-center rounded-xl bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                  <Glyph className="size-5">
                    <rect width="7" height="9" x="3" y="3" rx="1" />
                    <rect width="7" height="5" x="14" y="3" rx="1" />
                    <rect width="7" height="9" x="14" y="12" rx="1" />
                    <rect width="7" height="5" x="3" y="16" rx="1" />
                  </Glyph>
                </div>
                <div>
                  <h3 id="palette-title" className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Navigation Menu
                  </h3>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Jump to a section, profile or action</p>
                </div>
              </div>
              <div className="flex h-12 items-center gap-2 border-b border-black/30 px-3 dark:border-white/[0.15]">
                <Glyph className="size-4 opacity-50">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.3-4.3" />
                </Glyph>
                <input
                  ref={input}
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value)
                    setActive(0)
                  }}
                  placeholder="Search sections, profiles..."
                  aria-label="Search commands"
                  aria-controls="palette-list"
                  aria-activedescendant={matches[active] ? `palette-${active}` : undefined}
                  role="combobox"
                  aria-expanded="true"
                  className="flex h-12 w-full rounded-md border-none bg-transparent py-3 text-sm outline-hidden placeholder:text-zinc-500 dark:placeholder:text-zinc-400"
                />
              </div>
              <div id="palette-list" role="listbox" aria-label="Suggestions" className="max-h-[300px] scroll-py-1 overflow-x-hidden overflow-y-auto p-2">
                {matches.length === 0 && <p className="py-6 text-center text-sm text-zinc-500">No results found.</p>}
                {groups.map((group) => (
                  <div key={group} role="presentation" className="overflow-hidden p-1 text-zinc-900 dark:text-zinc-50">
                    <div aria-hidden="true" className="px-2 py-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                      {group}
                    </div>
                    <div role="group" aria-label={group}>
                      {matches
                        .filter((command) => command.group === group)
                        .map((command) => {
                          const index = matches.indexOf(command)
                          const selected = index === active
                          return (
                            <div
                              key={command.label}
                              id={`palette-${index}`}
                              role="option"
                              aria-selected={selected}
                              onMouseMove={() => setActive(index)}
                              onClick={() => run(command)}
                              className={`relative flex cursor-pointer items-center gap-2 rounded-lg px-2 py-3 text-sm outline-hidden select-none ${selected ? 'bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50' : ''}`}
                            >
                              <span className="mr-2 text-zinc-500">{command.icon}</span>
                              <span>{command.label}</span>
                              {command.key && (
                                <span className={`${MONO} ml-auto rounded border border-zinc-200 bg-zinc-100 px-1.5 py-0.5 text-[10px] tracking-widest text-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400`}>
                                  shift + {command.key}
                                </span>
                              )}
                            </div>
                          )
                        })}
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-between border-t border-zinc-100 bg-zinc-50/50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900/50">
                <div className="flex items-center gap-4 text-[10px] text-zinc-500">
                  <div className="flex items-center gap-1">
                    <Glyph className="size-3">
                      <path d="m5 12 7-7 7 7M12 19V5" />
                    </Glyph>
                    <Glyph className="size-3">
                      <path d="M12 5v14M19 12l-7 7-7-7" />
                    </Glyph>
                    <span>to navigate</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Glyph className="size-3">
                      <path d="M20 4v7a4 4 0 0 1-4 4H4M9 10l-5 5 5 5" />
                    </Glyph>
                    <span>to select</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                  <span className={MONO}>esc</span>
                  <span>to close</span>
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={close}
              className="absolute top-4 right-4 rounded-md text-zinc-500 opacity-70 transition-opacity hover:opacity-100 focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2 focus:outline-none dark:text-zinc-400"
            >
              <Glyph>
                <path d="M18 6 6 18M6 6l12 12" />
              </Glyph>
              <span className="sr-only">Close</span>
            </button>
          </div>
        </>
      )}
    </>
  )
}

/** The ⌘K key in the header, opening the menu when pressed. */
export const PaletteKey = ({ onOpen }: { onOpen: () => void }) => {
  return (
    <button type="button" onClick={onOpen} aria-label="Open the command menu" className="group relative cursor-pointer transition-all duration-300 active:scale-95">
      <div className="pointer-events-none absolute -inset-[4.5px] rounded-[9px] border border-black/5 transition-colors duration-300 group-hover:border-black/10 dark:border-white/5 dark:group-hover:border-white/10" />
      <div
        className={`relative flex items-center gap-1.5 rounded-[5px] border border-black/5 bg-zinc-50 px-3 py-1 ${MONO} text-[11px] font-medium text-zinc-500 shadow-sm shadow-black/20 transition-all duration-300 hover:bg-zinc-100 hover:text-zinc-900 dark:border-white/5 dark:bg-[#09090b] dark:text-zinc-400 dark:shadow-lg dark:shadow-black/80 dark:hover:bg-[#121214] dark:hover:text-zinc-100`}
      >
        <span className="mt-[0.5px] leading-none">⌘</span>
        <span className="mt-[0.5px] leading-none">K</span>
      </div>
    </button>
  )
}
