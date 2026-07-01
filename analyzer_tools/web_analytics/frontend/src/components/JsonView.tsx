import { Fragment, type ReactNode } from 'react'
import { parseJson, type JsonEntry, type JsonNode } from '../format/json'

const INDENT = '  '

// Pretty-printed, syntax-highlighted JSON. Falls back to raw text when the
// body isn't valid JSON (error pages, plain strings, empty bodies).
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
      {renderValue(tree, 0)}
    </pre>
  )
}

function Punct({ children }: { children: ReactNode }) {
  return <span className="tok-punct">{children}</span>
}

function renderValue(node: JsonNode, depth: number): ReactNode {
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
      return renderArray(node.items, depth)
    case 'object':
      return renderObject(node.entries, depth)
  }
}

function renderArray(items: JsonNode[], depth: number): ReactNode {
  if (items.length === 0) {
    return (
      <>
        <Punct>[</Punct>
        <Punct>]</Punct>
      </>
    )
  }
  const pad = INDENT.repeat(depth + 1)
  const closePad = INDENT.repeat(depth)
  return (
    <>
      <Punct>[</Punct>
      {'\n'}
      {items.map((item, idx) => (
        <Fragment key={idx}>
          {pad}
          {renderValue(item, depth + 1)}
          {idx < items.length - 1 && <Punct>,</Punct>}
          {'\n'}
        </Fragment>
      ))}
      {closePad}
      <Punct>]</Punct>
    </>
  )
}

function renderObject(entries: JsonEntry[], depth: number): ReactNode {
  if (entries.length === 0) {
    return (
      <>
        <Punct>{'{'}</Punct>
        <Punct>{'}'}</Punct>
      </>
    )
  }
  const pad = INDENT.repeat(depth + 1)
  const closePad = INDENT.repeat(depth)
  return (
    <>
      <Punct>{'{'}</Punct>
      {'\n'}
      {entries.map((entry, idx) => (
        <Fragment key={idx}>
          {pad}
          <span className="tok-key">{JSON.stringify(entry.key)}</span>
          <Punct>: </Punct>
          {renderValue(entry.value, depth + 1)}
          {idx < entries.length - 1 && <Punct>,</Punct>}
          {'\n'}
        </Fragment>
      ))}
      {closePad}
      <Punct>{'}'}</Punct>
    </>
  )
}
