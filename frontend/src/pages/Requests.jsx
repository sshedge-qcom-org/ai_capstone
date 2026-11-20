import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { AsyncState, Badge, date, money, useApi } from '../components/Async'
import Pagination from '../components/Pagination'

export default function Requests() {
  const { user } = useAuth()
  const [offset, setOffset] = useState(0)
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const state = useApi(`/requests?limit=20&offset=${offset}&search=${encodeURIComponent(search)}${status ? `&status=${status}` : ''}`)
  return <>
    <div className="row between"><div><p className="eyebrow">REQUESTS & APPROVALS</p><h1>Purchase requests</h1></div>
      {user.role === 'employee' && <Link className="button" to="/requests/new">+ New request</Link>}</div>
    <section className="card">
      <div className="grid" style={{ marginTop: 0 }}>
        <label>Search requests<input type="search" value={search} maxLength={120} onChange={e => { setSearch(e.target.value); setOffset(0) }} /></label>
        <label>Status<select value={status} onChange={e => { setStatus(e.target.value); setOffset(0) }}>
          <option value="">All statuses</option>{['pending', 'approved', 'revision', 'rejected', 'ordered'].map(s => <option key={s}>{s}</option>)}
        </select></label>
      </div>
      <AsyncState {...state}>{state.data && <>
        <div className="table-wrap"><table><caption className="sr-only">Visible purchase requests</caption><thead><tr>
          <th>Request</th><th>Category</th><th>Budget</th><th>Status</th><th>Created</th>
        </tr></thead><tbody>{state.data.map(row => <tr key={row.id}><td><Link to={`/requests/${row.id}`}>#{row.id} · {row.title}</Link></td>
          <td>{row.category}</td><td>{money(row.estimated_budget)}</td><td><Badge>{row.status}</Badge></td><td>{date(row.created_at)}</td></tr>)}</tbody></table></div>
        {!state.data.length && <p>No requests match your filters.</p>}
        <Pagination offset={offset} setOffset={setOffset} count={state.data.length} />
      </>}</AsyncState>
    </section>
  </>
}
