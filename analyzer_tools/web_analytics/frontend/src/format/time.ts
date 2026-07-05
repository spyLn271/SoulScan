const pad2 = (n: number) => String(n).padStart(2, '0')

export function hms(d: Date): string {
  return `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`
}

export function fmtTs(ms: number): string {
  const d = new Date(ms)
  return `${hms(d)}.${String(d.getMilliseconds()).padStart(3, '0')}`
}
