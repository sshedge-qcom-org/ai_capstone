import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { errorMessage } from '../api/client'

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function signOut() {
    setBusy(true); setError('')
    try { await logout() } catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <>
    <a className="skip" href="#main">Skip to content</a>
    <header className="topbar"><Link className="brand" to="/">Procure<span>AI</span></Link>
      {user ? <div className="row"><span>{user.full_name} <span className="badge">{user.role}</span></span>
        <button className="secondary" disabled={busy} onClick={signOut}>Sign out</button></div>
        : <span className="muted">Your procurement, connected.</span>}
    </header>
    {user && <nav aria-label="Main navigation" className="nav"><NavLink to="/dashboard">Overview</NavLink>
      {user.role !== 'vendor' && <NavLink to="/requests">Purchase requests</NavLink>}
      {user.role !== 'vendor' && <NavLink to="/suppliers">Suppliers</NavLink>}
      <NavLink to="/orders">Orders</NavLink>
      {user.role === 'admin' && <NavLink to="/admin">Administration</NavLink>}
    </nav>}
    <main id="main">{error && <p className="error" role="alert">{error}</p>}{children}</main>
  </>
}
