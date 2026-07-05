// CRC-32 (IEEE, zlib-compatible) over a UTF-8 string. Returns the unsigned
// value; venues encode it either unsigned (python zlib.crc32) or as a signed
// int32 (okx wire), so compare with crcMatches.

const TABLE = (() => {
  const t = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    t[n] = c >>> 0
  }
  return t
})()

export function crc32(s: string): number {
  const bytes = new TextEncoder().encode(s)
  let c = 0xffffffff
  for (let i = 0; i < bytes.length; i++) {
    c = TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8)
  }
  return (c ^ 0xffffffff) >>> 0
}

export function crcMatches(computedUnsigned: number, wire: number): boolean {
  return wire === computedUnsigned || wire === (computedUnsigned | 0)
}
