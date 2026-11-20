import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, errorMessage } from '../api/client'
import { AsyncState, useApi } from './Async'

export default function Recommendations({ requestId }) {
  const state = useApi(`/requests/${requestId}/recommendations`)
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function createOrder(supplier) {
    if (!window.confirm(`Create an order with ${supplier.company_name} at the request's estimated total budget?`)) return
    setBusy(true); setError('')
    try {
      const { data } = await api.post('/orders', { request_id: Number(requestId), supplier_id: supplier.id })
      navigate(`/orders/${data.id}`)
    } catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <section className="card"><p className="eyebrow">EXPLAINABLE DECISION SUPPORT</p><h2>Recommended suppliers</h2>
    <p className="muted">Ranked for value using 40% price, 25% rating, 20% delivery speed and 15% reliability. Scores are not supplier quotes.</p>
    {error && <p role="alert" className="error">{error}</p>}
    <AsyncState {...state}>{state.data && (state.data.length ? <div className="grid">{state.data.map((row, i) => <article className="card" key={row.supplier.id}>
      <p className="eyebrow">#{i + 1} MATCH</p><h3><Link to={`/suppliers/${row.supplier.id}`}>{row.supplier.company_name}</Link></h3>
      <div className="kpi">{Number(row.score).toFixed(2)}<span className="muted"> / 100</span></div>
      <p className="muted">{row.explanation}</p>
      <details><summary>Score contributions</summary><ul>{Object.entries(row.contributions).map(([name, value]) => <li key={name}>{name}: {Number(value).toFixed(2)} points</li>)}</ul></details>
      <button style={{ marginTop: '1rem' }} disabled={busy} onClick={() => createOrder(row.supplier)}>{busy ? 'Creating…' : 'Select & create order'}</button>
    </article>)}</div> : <p>No suppliers match this category. Ask an administrator to add suppliers.</p>)}</AsyncState>
  </section>
}
