import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, errorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { AsyncState, useApi } from '../components/Async'
import Pagination from '../components/Pagination'

export default function Suppliers() {
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [creating, setCreating] = useState(false)
  const { user } = useAuth()
  const categories = useApi('/categories')
  const state = useApi(`/suppliers?offset=${offset}&limit=20&search=${encodeURIComponent(search)}${category ? `&category=${encodeURIComponent(category)}` : ''}`)
  return <><div className="row between"><div><p className="eyebrow">YOUR SUPPLY NETWORK</p><h1>Supplier directory</h1></div>
    {user.role === 'admin' && <button onClick={() => setCreating(!creating)}>{creating ? 'Close form' : '+ Add supplier'}</button>}</div>
    {creating && <SupplierForm onSaved={() => { setCreating(false); state.reload() }} />}
    <section className="card">
      <div className="grid" style={{ marginTop: 0 }}><label>Search suppliers<input type="search" value={search} maxLength={120} onChange={e => { setSearch(e.target.value); setOffset(0) }} /></label>
        <AsyncState {...categories}><label>Category<select value={category} onChange={e => { setCategory(e.target.value); setOffset(0) }}><option value="">All categories</option>{categories.data?.map(c => <option key={c}>{c}</option>)}</select></label></AsyncState></div>
      <AsyncState {...state}>{state.data && <>
        <div className="table-wrap"><table><caption className="sr-only">Supplier directory</caption><thead><tr><th>Supplier</th><th>Category</th><th>Rating</th><th>Delivery</th><th>Reliability</th></tr></thead>
          <tbody>{state.data.map(row => <tr key={row.id}><td><Link to={`/suppliers/${row.id}`}>{row.company_name}</Link></td><td>{row.category}</td><td>{row.rating} / 5</td><td>{row.average_delivery_days} days</td><td>{row.reliability_score}%</td></tr>)}</tbody></table></div>
        {!state.data.length && <p>No suppliers match your filters.</p>}
        <Pagination offset={offset} setOffset={setOffset} count={state.data.length} />
      </>}</AsyncState>
    </section>
  </>
}

export function SupplierDetail() {
  const { id } = useParams()
  const state = useApi(`/suppliers/${id}`)
  const { user } = useAuth()
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const supplier = state.data
  async function remove() {
    if (!window.confirm('Delete this supplier? Linked suppliers cannot be deleted.')) return
    setError(''); setBusy(true)
    try { await api.delete(`/suppliers/${id}`); navigate('/suppliers') }
    catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <><Link to="/suppliers">← Supplier directory</Link><AsyncState {...state}>{supplier && <section className="card" style={{ marginTop: '1rem' }}>
    <h1>{supplier.company_name}</h1><p className="muted">Supplier #{supplier.id} · {supplier.category}</p>
    <div className="grid">{[['Rating', `${supplier.rating} / 5`], ['Price value score', `${supplier.average_price_score} / 100`], ['Average delivery', `${supplier.average_delivery_days} days`], ['Reliability', `${supplier.reliability_score}%`]].map(([label, value]) => <div key={label}><p className="muted">{label}</p><h2>{value}</h2></div>)}</div>
    <p>{supplier.contact_person} · <a href={`mailto:${supplier.email}`}>{supplier.email}</a></p>
    {error && <p role="alert" className="error">{error}</p>}
    {user.role === 'admin' && <div className="row"><button onClick={() => setEditing(!editing)}>{editing ? 'Cancel editing' : 'Edit supplier'}</button><button className="danger" disabled={busy} onClick={remove}>Delete supplier</button></div>}
    {editing && <SupplierForm initial={supplier} onSaved={() => { setEditing(false); state.reload() }} />}
  </section>}</AsyncState></>
}

function SupplierForm({ initial, onSaved }) {
  const categories = useApi('/categories')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true)
    const data = Object.fromEntries(new FormData(event.currentTarget))
    data.average_delivery_days = Number(data.average_delivery_days)
    try {
      if (initial) await api.patch(`/suppliers/${initial.id}`, data)
      else await api.post('/suppliers', data)
      onSaved()
    } catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <section className="card" style={{ margin: '1rem 0' }}><h2>{initial ? 'Update supplier' : 'New supplier'}</h2><AsyncState {...categories}>
    {error && <p className="error" role="alert">{error}</p>}
    <form className="form" onSubmit={submit}>
      <label>Company name<input name="company_name" required maxLength={120} defaultValue={initial?.company_name} /></label>
      <label>Category<select name="category" required defaultValue={initial?.category || ''}><option disabled value="">Choose category</option>{categories.data?.map(c => <option key={c}>{c}</option>)}</select></label>
      <div className="grid" style={{ marginTop: 0 }}>{[
        ['rating', 'Rating (0–5)', 0, 5, '.01'], ['average_price_score', 'Price value (0–100)', 0, 100, '.01'],
        ['average_delivery_days', 'Delivery days', 1, 365, '1'], ['reliability_score', 'Reliability (0–100)', 0, 100, '.01'],
      ].map(([name, label, min, max, step]) => <label key={name}>{label}<input name={name} type="number" min={min} max={max} step={step} required defaultValue={initial?.[name]} /></label>)}</div>
      <label>Contact person<input name="contact_person" required maxLength={120} defaultValue={initial?.contact_person} /></label>
      <label>Contact email<input name="email" type="email" required defaultValue={initial?.email} /></label>
      <button disabled={busy || !categories.data?.length}>{busy ? 'Saving…' : 'Save supplier'}</button>
    </form>
  </AsyncState></section>
}
