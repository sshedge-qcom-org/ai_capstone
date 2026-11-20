import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { api, errorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export default function AuthPage({ register = false }) {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/dashboard" replace />
  async function submit(event) {
    event.preventDefault()
    setError(''); setBusy(true)
    const data = Object.fromEntries(new FormData(event.currentTarget))
    try {
      if (register) await api.post('/auth/register', data)
      await login(data.email, data.password)
      navigate(location.state?.from || '/dashboard', { replace: true })
    } catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <section className="card auth-card">
    <p className="eyebrow">WELCOME TO PROCUREAI</p>
    <h1>{register ? 'Create your account' : 'Welcome back'}</h1>
    <p className="muted">{register ? 'Register as an employee. Your administrator assigns your manager.' : 'Sign in to your procurement workspace.'}</p>
    {error && <p className="error" role="alert">{error}</p>}
    <form className="form" onSubmit={submit}>
      {register && <label>Full name<input name="full_name" required maxLength={120} autoComplete="name" /></label>}
      <label>Email<input name="email" type="email" required autoComplete="username" /></label>
      <label>Password<input name="password" type="password" required minLength={register ? 10 : 1} maxLength={72} autoComplete={register ? 'new-password' : 'current-password'} /></label>
      {register && <p className="muted">Use 10–72 characters, including an uppercase letter and a number.</p>}
      <button disabled={busy}>{busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'}</button>
    </form>
    <p className="muted" style={{ marginTop: '1rem' }}>{register ? 'Already registered?' : 'New to the platform?'}{' '}
      <Link to={register ? '/login' : '/register'}>{register ? 'Sign in' : 'Create an account'}</Link></p>
  </section>
}
