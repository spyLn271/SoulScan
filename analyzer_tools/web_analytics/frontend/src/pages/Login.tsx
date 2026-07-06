import { type FormEvent, useState } from 'react'
import { login } from '../auth'

export function Login() {
  const [name, setName] = useState('')
  const [secret, setSecret] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = !pending && name.trim() !== '' && secret !== ''

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setPending(true)
    setError(null)
    const r = await login(name.trim(), secret)
    if (!r.ok) {
      setError(r.error)
      setPending(false)
    }
    // on success useAuth() re-renders App and this page unmounts
  }

  return (
    <div className="login">
      <form className="panel login__panel" onSubmit={onSubmit}>
        <div className="panel__head">
          <h2>sign in</h2>
        </div>

        <label className="field">
          <span className="field__label">name</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="username"
            autoFocus
            spellCheck={false}
          />
        </label>

        <label className="field">
          <span className="field__label">secret</span>
          <input
            type="password"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            autoComplete="current-password"
          />
        </label>

        {error && <div className="notice notice--err login__error">sign in failed — {error}</div>}

        <button className="btn" type="submit" disabled={!canSubmit}>
          {pending ? 'signing in…' : 'sign in'}
        </button>
      </form>
    </div>
  )
}
