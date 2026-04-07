import { FormEvent, useEffect, useState } from 'react'
import Dashboard from './Dashboard'
import './App.css'

const STORAGE_KEY = 'lablens_api_key'

function App() {
  const [token, setToken] = useState(
    () => localStorage.getItem(STORAGE_KEY) ?? '',
  )
  const [draft, setDraft] = useState('')

  useEffect(() => {
    if (token) {
      localStorage.setItem(STORAGE_KEY, token)
    }
  }, [token])

  function handleConnect(e: FormEvent) {
    e.preventDefault()
    const trimmed = draft.trim()
    if (!trimmed) return
    localStorage.setItem(STORAGE_KEY, trimmed)
    setToken(trimmed)
  }

  function handleDisconnect() {
    localStorage.removeItem(STORAGE_KEY)
    setToken('')
    setDraft('')
  }

  if (!token) {
    return (
      <main className="token-shell">
        <section className="token-card">
          <div className="eyebrow">se-toolkit-hackathon</div>
          <h1>Turn lab progress into clear next actions.</h1>
          <p>
            Connect with your LMS API key to see lab health, weak spots, and an
            assistant that explains what to do next.
          </p>
          <form className="token-form" onSubmit={handleConnect}>
            <label htmlFor="api-key">API key</label>
            <input
              id="api-key"
              type="password"
              placeholder="Paste your LMS API key"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
            />
            <button type="submit">Open dashboard</button>
          </form>
          <p className="token-note">
            The key is stored only in your browser. Use the same backend that you
            already ran in the previous labs.
          </p>
          <p className="token-note">
            Local demo key: <strong>my-secret-api-key</strong>
          </p>
        </section>
      </main>
    )
  }

  return (
    <Dashboard token={token} onDisconnect={handleDisconnect} />
  )
}

export default App
