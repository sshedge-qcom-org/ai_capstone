import { createContext, useContext, useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { acceptSession, api, configureSession, errorMessage, refreshSession } from '../api/client'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => {
    configureSession(setUser)
    refreshSession().catch(error => {
      if (error.response?.status !== 401) setError(errorMessage(error))
    }).finally(() => setLoading(false))
    return () => configureSession(() => {})
  }, [])
  async function login(email, password) {
    const { data } = await api.post('/auth/login', { email, password })
    acceptSession(data)
    setError('')
  }
  async function logout() {
    await api.post('/auth/logout')
    acceptSession(null)
  }
  return <AuthContext.Provider value={{ user, loading, error, login, logout }}>{children}</AuthContext.Provider>
}

export function Protected({ roles, children }) {
  const { user, loading, error } = useAuth()
  const location = useLocation()
  if (loading) return <p role="status">Restoring your session…</p>
  if (error) return <div role="alert" className="error">{error} <button onClick={() => window.location.reload()}>Retry</button></div>
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />
  if (roles && !roles.includes(user.role)) return <section className="card"><h1>Access restricted</h1><p>Your role cannot open this page.</p></section>
  return children
}
