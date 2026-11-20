import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, errorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { AsyncState, Badge, date, money, useApi } from '../components/Async'
import Pagination from '../components/Pagination'

const steps = ['created', 'processing', 'shipped', 'delivered']

export default function Orders() {
  const [offset, setOffset] = useState(0)
  const [status, setStatus] = useState('')
  const state = useApi(`/orders?limit=20&offset=${offset}${status ? `&status=${status}` : ''}`)
  return <><p className="eyebrow">FULFILMENT & DELIVERY</p><h1>Purchase orders</h1>
    <section className="card"><label style={{ maxWidth: 320 }}>Status<select value={status} onChange={e => { setStatus(e.target.value); setOffset(0) }}><option value="">All statuses</option>{steps.map(s => <option key={s}>{s}</option>)}</select></label>
      <AsyncState {...state}>{state.data && <>
        <div className="table-wrap"><table><caption className="sr-only">Visible purchase orders</caption><thead><tr><th>Order</th><th>Request</th><th>Supplier</th><th>Amount</th><th>Status</th><th>Ordered</th></tr></thead>
          <tbody>{state.data.map(row => <tr key={row.id}><td><Link to={`/orders/${row.id}`}>PO-{String(row.id).padStart(5, '0')}</Link></td><td>#{row.request_id}</td><td>#{row.supplier_id}</td><td>{money(row.amount)}</td><td><Badge>{row.status}</Badge></td><td>{date(row.order_date)}</td></tr>)}</tbody></table></div>
        {!state.data.length && <p>No orders match your filters.</p>}
        <Pagination offset={offset} setOffset={setOffset} count={state.data.length} />
      </>}</AsyncState>
    </section>
  </>
}

export function OrderDetail() {
  const { id } = useParams()
  const state = useApi(`/orders/${id}`)
  const { user } = useAuth()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const order = state.data
  const next = order && steps[steps.indexOf(order.status) + 1]
  async function advance() {
    if (!window.confirm(`Mark this order as ${next}?`)) return
    setError(''); setBusy(true)
    try { await api.patch(`/orders/${id}/status`, { status: next }); state.reload() }
    catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <><Link to="/orders">← Purchase orders</Link><AsyncState {...state}>{order && <div className="stack" style={{ marginTop: '1rem' }}>
    <section className="card"><div className="row between"><h1>PO-{String(order.id).padStart(5, '0')}</h1><Badge>{order.status}</Badge></div>
      <h2>{order.request_title}</h2><p>{order.supplier_name}</p>
      <div className="grid"><div><p className="muted">Approved estimated total</p><h2>{money(order.amount)}</h2></div>
        <div><p className="muted">Order date</p><h2>{date(order.order_date)}</h2></div><div><p className="muted">Delivered</p><h2>{date(order.delivery_date)}</h2></div></div>
      <p className="muted">Order value snapshots the approved request estimate. It is not a negotiated supplier quote.</p>
      {user.role !== 'vendor' && <Link to={`/requests/${order.request_id}`}>View purchase request</Link>}
    </section>
    <section className="card"><h2>Fulfilment progress</h2><ol className="grid" aria-label="Fulfilment steps">{steps.map((step, index) => <li key={step} className="card" aria-current={order.status === step ? 'step' : undefined}>
      <span className="step">{index <= steps.indexOf(order.status) ? '✓' : index + 1}</span><Badge>{step}</Badge></li>)}</ol>
      {error && <p role="alert" className="error">{error}</p>}
      {['vendor', 'admin'].includes(user.role) && next && <button style={{ marginTop: '1rem' }} disabled={busy} onClick={advance}>{busy ? 'Updating…' : `Mark as ${next}`}</button>}
    </section>
    <section className="card"><h2>Status history</h2><ol>{order.history.map(event => <li key={event.id}><Badge>{event.status}</Badge> · {date(event.created_at)} · user #{event.actor_id}</li>)}</ol></section>
  </div>}</AsyncState></>
}
