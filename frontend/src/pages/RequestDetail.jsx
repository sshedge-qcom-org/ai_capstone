import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, errorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { AsyncState, Badge, date, money, useApi } from '../components/Async'

export default function RequestDetail() {
  const { id } = useParams()
  const state = useApi(`/requests/${id}`)
  const { user } = useAuth()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [reason, setReason] = useState('')
  const request = state.data
  async function decide(decision) {
    setError(''); setBusy(true)
    try { await api.post(`/requests/${id}/decision`, { decision, reason }); state.reload() }
    catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <><Link to="/requests">← Purchase requests</Link><AsyncState {...state}>{request && <div className="stack" style={{ marginTop: '1rem' }}>
    <section className="card">
      <div className="row between"><h1>{request.title}</h1><Badge>{request.status}</Badge></div>
      <p className="muted">Request #{request.id} · {request.category} · Created {date(request.created_at)}</p>
      <p style={{ whiteSpace: 'pre-wrap' }}>{request.description}</p>
      <div className="grid"><div><span className="muted">Estimated total budget</span><h2>{money(request.estimated_budget)}</h2></div>
        <div><span className="muted">Quantity</span><h2>{request.quantity}</h2></div><div><span className="muted">Target delivery</span><h2>{date(request.target_delivery_date)}</h2></div></div>
      {user.id === request.requested_by && ['pending', 'revision'].includes(request.status) && <Link className="button" to={`/requests/${id}/edit`}>Edit request</Link>}
    </section>
    {['manager', 'admin'].includes(user.role) && request.status === 'pending' && <section className="card"><h2>Review request</h2>
      {error && <p role="alert" className="error">{error}</p>}
      <label>Review note (required for rejection or revision)<textarea value={reason} maxLength={2000} onChange={e => setReason(e.target.value)} /></label>
      <div className="row" style={{ marginTop: '1rem' }}><button disabled={busy} onClick={() => decide('approved')}>Approve</button>
        <button className="secondary" disabled={busy || !reason.trim()} onClick={() => decide('revision')}>Send for revision</button>
        <button className="danger" disabled={busy || !reason.trim()} onClick={() => decide('rejected')}>Reject</button></div>
    </section>}
    <section className="card"><h2>Decision history</h2>{request.history.length ? <ol>{request.history.map(event => <li key={event.id}>
      <Badge>{event.decision}</Badge> by user #{event.actor_id} · {date(event.created_at)}<p>{event.reason}</p></li>)}</ol> : <p>No decisions yet.</p>}</section>
  </div>}</AsyncState></>
}
