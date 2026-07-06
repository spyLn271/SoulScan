import { useState, type ReactNode } from 'react'
import { SorTester } from './pages/SorTester'
import { NetworkResourceTester } from './pages/NetworkResourceTester'
import { WsOrderBooks } from './pages/WsOrderBooks'
import { IconRoute, IconInfo, IconCoins, IconStream } from './components/icons'
import { FloatingCards } from './components/FloatingCards'
import { Login } from './pages/Login'
import { clearAuth, useAuth } from './auth'
import type { HttpMethod } from './components/EndpointChip'

interface Test {
  id: string
  label: string
  group: 'HTTP' | 'STREAM'
  method: HttpMethod
  icon: ReactNode
  render: () => ReactNode
}

const TESTS: readonly Test[] = [
  {
    id: 'sor',
    label: 'SOR',
    group: 'HTTP',
    method: 'POST',
    icon: <IconRoute />,
    render: () => <SorTester />,
  },
  {
    id: 'metadata',
    label: 'Metadata',
    group: 'HTTP',
    method: 'GET',
    icon: <IconInfo />,
    render: () => <NetworkResourceTester key="/v1/metadata" basePath="/v1/metadata" />,
  },
  {
    id: 'tokens',
    label: 'Tokens',
    group: 'HTTP',
    method: 'GET',
    icon: <IconCoins />,
    render: () => <NetworkResourceTester key="/v1/tokens" basePath="/v1/tokens" />,
  },
  {
    id: 'ws',
    label: 'Order books',
    group: 'STREAM',
    method: 'WS',
    icon: <IconStream />,
    render: () => <WsOrderBooks />,
  },
]

const GROUPS = ['HTTP', 'STREAM'] as const

function initialTab(): string {
  const h = window.location.hash.slice(1)
  return TESTS.find((t) => t.id === h)?.id ?? TESTS[0].id
}

export default function App() {
  const [active, setActive] = useState<string>(initialTab)
  const auth = useAuth()
  const current = TESTS.find((t) => t.id === active) ?? TESTS[0]

  function select(id: string) {
    setActive(id)
    window.history.replaceState(null, '', `#${id}`)
  }

  if (auth === null) return <Login />

  return (
    <>
      <div className="app">
      <aside className="sidebar">
        <nav className="sidebar__nav" aria-label="endpoints">
          {GROUPS.map((g) => (
            <div key={g} className="sidebar__group">
              <div className="sidebar__group-label">{g}</div>
              {TESTS.filter((t) => t.group === g).map((t) => (
                <button
                  key={t.id}
                  className="nav-item"
                  aria-current={t.id === active ? 'page' : undefined}
                  onClick={() => select(t.id)}
                >
                  {t.icon}
                  <span>{t.label}</span>
                  <span className={`method method--${t.method.toLowerCase()}`}>
                    {t.method}
                  </span>
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar__user">
          <span className="sidebar__user-name">{auth.name}</span>
          <button
            type="button"
            className="btn btn--ghost btn--xs"
            onClick={clearAuth}
          >
            sign out
          </button>
        </div>
      </aside>

        <main className="app-main">{current.render()}</main>
      </div>
      <FloatingCards />
    </>
  )
}
