import { useCallback, useEffect, useState } from 'react'
import { api, errorMessage } from '../api/client'

export function useApi(path) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)
  const reload = useCallback(() => setVersion(v => v + 1), [])
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError('')
    api.get(path, { signal: controller.signal }).then(({ data }) => setData(data))
      .catch(error => { if (!controller.signal.aborted) setError(errorMessage(error)) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [path, version])
  return { data, error, loading, reload }
}

export function AsyncState({ loading, error, reload, children }) {
  if (loading) return <p role="status">Loading workspace data…</p>
  if (error) return <div role="alert" className="error">{error} <button onClick={reload}>Try again</button></div>
  return children
}

export const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value))
export const date = value => value ? new Date(value.includes('T') && !/(Z|[+-]\d{2}:\d{2})$/i.test(value) ? `${value}Z` : value).toLocaleDateString(undefined, { timeZone: 'UTC' }) : '—'
export const Badge = ({ children }) => <span className="badge">{children}</span>
