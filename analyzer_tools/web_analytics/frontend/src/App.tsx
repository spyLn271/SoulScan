import { useState } from 'react'
import { SorTester } from './pages/SorTester'
import { NetworkResourceTester } from './pages/NetworkResourceTester'

const TESTS = [
  { id: 'sor', label: 'SOR quote', render: () => <SorTester /> },
  {
    id: 'metadata',
    label: 'Metadata · network',
    render: () => <NetworkResourceTester basePath="/v1/metadata" />,
  },
  {
    id: 'tokens',
    label: 'Tokens · network',
    render: () => <NetworkResourceTester basePath="/v1/tokens" />,
  },
] as const

export default function App() {
  const [active, setActive] = useState<string>(TESTS[0].id)
  const current = TESTS.find((t) => t.id === active) ?? TESTS[0]

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-brand">
          <span className="app-brand__name">SoulScan</span>
        </div>
      </header>

      <nav className="tabs">
        {TESTS.map((t) => (
          <button
            key={t.id}
            className={`tab ${t.id === active ? 'tab--active' : ''}`}
            onClick={() => setActive(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="app-main">{current.render()}</main>
    </div>
  )
}
