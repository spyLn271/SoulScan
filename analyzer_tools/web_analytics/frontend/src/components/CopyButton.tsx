import { useRef, useState } from 'react'

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const timer = useRef<number | undefined>(undefined)

  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      // clipboard API needs a secure context — fall back for plain-http hosts
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      ta.remove()
    }
    setCopied(true)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setCopied(false), 1200)
  }

  return (
    <button type="button" className="btn btn--ghost btn--xs" onClick={copy}>
      {copied ? 'copied' : 'copy'}
    </button>
  )
}
