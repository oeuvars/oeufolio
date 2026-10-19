/** Messages' typing bubble: three dots in a grey bubble trailing two smaller ones, while I write back. */
export const Typing = () => {
  return (
    <div data-side="me" className="chat-arrive mt-3.5 ml-2 flex" role="status">
      <span className="sr-only">Anurag is typing</span>
      <div aria-hidden="true" className="relative flex h-[38px] items-center gap-[5px] rounded-[19px] bg-[var(--chat-in)] px-[14px]">
        <span className="chat-dot size-2 rounded-full bg-[var(--chat-quiet)]" />
        <span className="chat-dot size-2 rounded-full bg-[var(--chat-quiet)]" />
        <span className="chat-dot size-2 rounded-full bg-[var(--chat-quiet)]" />
        <span className="absolute -bottom-px -left-px size-3 rounded-full bg-[var(--chat-in)]" />
        <span className="absolute -bottom-[7px] -left-[6px] size-1.5 rounded-full bg-[var(--chat-in)]" />
      </div>
    </div>
  )
}
