const base = {
  width: 16,
  height: 16,
  viewBox: '0 0 16 16',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
} as const

export function IconRoute() {
  return (
    <svg {...base}>
      <circle cx="3.5" cy="12.5" r="1.75" />
      <circle cx="12.5" cy="3.5" r="1.75" />
      <path d="M5.25 12.5H9a3 3 0 0 0 3-3V5.25" />
    </svg>
  )
}

export function IconInfo() {
  return (
    <svg {...base}>
      <circle cx="8" cy="8" r="6.25" />
      <path d="M8 7.5V11" />
      <path d="M8 5v.01" />
    </svg>
  )
}

export function IconCoins() {
  return (
    <svg {...base}>
      <circle cx="6" cy="6" r="4.25" />
      <path d="M11.6 5.9a4.25 4.25 0 1 1-5.7 5.7" />
    </svg>
  )
}

export function IconStream() {
  return (
    <svg {...base}>
      <path d="M1.75 8h2.5l2-4.5 3.5 9 2-4.5h2.5" />
    </svg>
  )
}
