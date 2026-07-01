// A big-integer-safe JSON parser for the response viewer.
//
// We deliberately do NOT use JSON.parse: it coerces every number to a JS
// `number`, which silently loses precision above 2^53 — and SOR responses can
// carry u128/u256 amounts. Here number tokens are preserved as their exact
// source text, so what you see is what the backend sent.

export type JsonNode =
  | { kind: 'string'; value: string }
  | { kind: 'number'; raw: string }
  | { kind: 'bool'; value: boolean }
  | { kind: 'null' }
  | { kind: 'array'; items: JsonNode[] }
  | { kind: 'object'; entries: JsonEntry[] }

export interface JsonEntry {
  key: string
  value: JsonNode
}

export function parseJson(text: string): JsonNode {
  const parser = new Parser(text)
  const node = parser.parseValue()
  parser.skipWs()
  if (!parser.atEnd()) throw new SyntaxError('unexpected trailing characters')
  return node
}

class Parser {
  private i = 0
  constructor(private readonly s: string) {}

  atEnd(): boolean {
    return this.i >= this.s.length
  }

  skipWs(): void {
    while (this.i < this.s.length) {
      const c = this.s[this.i]
      if (c === ' ' || c === '\t' || c === '\n' || c === '\r') this.i++
      else break
    }
  }

  parseValue(): JsonNode {
    this.skipWs()
    const c = this.s[this.i]
    if (c === '{') return this.parseObject()
    if (c === '[') return this.parseArray()
    if (c === '"') return { kind: 'string', value: this.parseString() }
    if (c === '-' || (c >= '0' && c <= '9')) {
      return { kind: 'number', raw: this.parseNumber() }
    }
    if (this.s.startsWith('true', this.i)) {
      this.i += 4
      return { kind: 'bool', value: true }
    }
    if (this.s.startsWith('false', this.i)) {
      this.i += 5
      return { kind: 'bool', value: false }
    }
    if (this.s.startsWith('null', this.i)) {
      this.i += 4
      return { kind: 'null' }
    }
    throw new SyntaxError(`unexpected token at index ${this.i}`)
  }

  private parseObject(): JsonNode {
    this.i++ // consume '{'
    const entries: JsonEntry[] = []
    this.skipWs()
    if (this.s[this.i] === '}') {
      this.i++
      return { kind: 'object', entries }
    }
    for (;;) {
      this.skipWs()
      if (this.s[this.i] !== '"') throw new SyntaxError('expected object key')
      const key = this.parseString()
      this.skipWs()
      if (this.s[this.i] !== ':') throw new SyntaxError('expected ":"')
      this.i++
      entries.push({ key, value: this.parseValue() })
      this.skipWs()
      const ch = this.s[this.i]
      if (ch === ',') {
        this.i++
        continue
      }
      if (ch === '}') {
        this.i++
        break
      }
      throw new SyntaxError('expected "," or "}"')
    }
    return { kind: 'object', entries }
  }

  private parseArray(): JsonNode {
    this.i++ // consume '['
    const items: JsonNode[] = []
    this.skipWs()
    if (this.s[this.i] === ']') {
      this.i++
      return { kind: 'array', items }
    }
    for (;;) {
      items.push(this.parseValue())
      this.skipWs()
      const ch = this.s[this.i]
      if (ch === ',') {
        this.i++
        continue
      }
      if (ch === ']') {
        this.i++
        break
      }
      throw new SyntaxError('expected "," or "]"')
    }
    return { kind: 'array', items }
  }

  private parseString(): string {
    this.i++ // consume opening quote
    let out = ''
    while (this.i < this.s.length) {
      const c = this.s[this.i++]
      if (c === '"') return out
      if (c === '\\') {
        const e = this.s[this.i++]
        switch (e) {
          case '"':
            out += '"'
            break
          case '\\':
            out += '\\'
            break
          case '/':
            out += '/'
            break
          case 'b':
            out += '\b'
            break
          case 'f':
            out += '\f'
            break
          case 'n':
            out += '\n'
            break
          case 'r':
            out += '\r'
            break
          case 't':
            out += '\t'
            break
          case 'u':
            out += String.fromCharCode(parseInt(this.s.slice(this.i, this.i + 4), 16))
            this.i += 4
            break
          default:
            throw new SyntaxError('invalid escape sequence')
        }
      } else {
        out += c
      }
    }
    throw new SyntaxError('unterminated string')
  }

  private parseNumber(): string {
    const start = this.i
    if (this.s[this.i] === '-') this.i++
    while (this.i < this.s.length && isNumberChar(this.s[this.i])) this.i++
    return this.s.slice(start, this.i)
  }
}

function isNumberChar(c: string): boolean {
  return (
    (c >= '0' && c <= '9') ||
    c === '.' ||
    c === 'e' ||
    c === 'E' ||
    c === '+' ||
    c === '-'
  )
}
