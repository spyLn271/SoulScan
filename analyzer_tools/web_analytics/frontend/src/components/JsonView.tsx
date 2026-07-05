import { Fragment, useState, type ReactNode } from 'react'
import { parseJson, type JsonEntry, type JsonNode } from '../format/json'

const INDENT = '  '
// Containers deeper than this start collapsed.
const EXPAND_DEPTH = 2
// Arrays render this many items up front; each "+ N more" click reveals more.
const CHUNK = 100
const CHUNK_STEP = 400

// Pretty-printed, syntax-highlighted JSON with collapsible containers.
// Falls back to raw text when the body isn't valid JSON.
export function JsonView({ text }: { text: string }) {
  let tree: JsonNode | null = null
  try {
    tree = parseJson(text)
  } catch {
    tree = null
  }

  if (tree === null) {
    return (
      <pre className="code-block code-block--scroll">
        {text || '(empty response body)'}
      </pre>
    )
  }

  return (
    <pre className="code-block code-block--scroll json-view">
      {/* key remounts the tree per body, so collapse state never bleeds
          between responses */}
      <NodeView key={text} node={tree} depth={0} />
    </pre>
  )
}

function Punct({ children }: { children: ReactNode }) {
  return <span className="tok-punct">{children}</span>
}

function Toggle({ open, onClick }: { open: boolean; onClick: () => void }) {
  return (
    <button type="button" className="json-toggle" aria-expanded={open} onClick={onClick}>
      {open ? '▾' : '▸'}
    </button>
  )
}

function NodeView({ node, depth }: { node: JsonNode; depth: number }) {
  switch (node.kind) {
    case 'string':
      return <span className="tok-string">{JSON.stringify(node.value)}</span>
    case 'number':
      return <span className="tok-number">{node.raw}</span>
    case 'bool':
      return <span className="tok-bool">{String(node.value)}</span>
    case 'null':
      return <span className="tok-null">null</span>
    case 'array':
      return <ArrayView items={node.items} depth={depth} />
    case 'object':
      return <ObjectView entries={node.entries} depth={depth} />
  }
}

function ArrayView({ items, depth }: { items: JsonNode[]; depth: number }) {
  const [open, setOpen] = useState(depth < EXPAND_DEPTH)
  const [shown, setShown] = useState(CHUNK)

  if (items.length === 0) {
    return (
      <>
        <Punct>[</Punct>
        <Punct>]</Punct>
      </>
    )
  }

  if (!open) {
    return (
      <>
        <Toggle open={false} onClick={() => setOpen(true)} />
        <Punct>[</Punct>
        <span className="json-count"> {items.length} {items.length === 1 ? 'item' : 'items'} </span>
        <Punct>]</Punct>
      </>
    )
  }

  const pad = INDENT.repeat(depth + 1)
  const closePad = INDENT.repeat(depth)
  const visible = items.slice(0, shown)
  const hidden = items.length - visible.length

  return (
    <>
      <Toggle open onClick={() => setOpen(false)} />
      <Punct>[</Punct>
      {'\n'}
      {visible.map((item, idx) => (
        <Fragment key={idx}>
          {pad}
          <NodeView node={item} depth={depth + 1} />
          {idx < items.length - 1 && <Punct>,</Punct>}
          {'\n'}
        </Fragment>
      ))}
      {hidden > 0 && (
        <>
          {pad}
          <button
            type="button"
            className="json-more"
            onClick={() => setShown((s) => s + CHUNK_STEP)}
          >
            + {hidden.toLocaleString('en-US')} more
          </button>
          {'\n'}
        </>
      )}
      {closePad}
      <Punct>]</Punct>
    </>
  )
}

function ObjectView({ entries, depth }: { entries: JsonEntry[]; depth: number }) {
  const [open, setOpen] = useState(depth < EXPAND_DEPTH)

  if (entries.length === 0) {
    return (
      <>
        <Punct>{'{'}</Punct>
        <Punct>{'}'}</Punct>
      </>
    )
  }

  if (!open) {
    return (
      <>
        <Toggle open={false} onClick={() => setOpen(true)} />
        <Punct>{'{'}</Punct>
        <span className="json-count"> {entries.length} {entries.length === 1 ? 'key' : 'keys'} </span>
        <Punct>{'}'}</Punct>
      </>
    )
  }

  const pad = INDENT.repeat(depth + 1)
  const closePad = INDENT.repeat(depth)

  return (
    <>
      <Toggle open onClick={() => setOpen(false)} />
      <Punct>{'{'}</Punct>
      {'\n'}
      {entries.map((entry, idx) => (
        <Fragment key={idx}>
          {pad}
          <span className="tok-key">{JSON.stringify(entry.key)}</span>
          <Punct>: </Punct>
          <NodeView node={entry.value} depth={depth + 1} />
          {idx < entries.length - 1 && <Punct>,</Punct>}
          {'\n'}
        </Fragment>
      ))}
      {closePad}
      <Punct>{'}'}</Punct>
    </>
  )
}
