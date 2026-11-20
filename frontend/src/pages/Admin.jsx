import { useState } from 'react'
import { api, errorMessage } from '../api/client'
import { AsyncState, useApi } from '../components/Async'
import Pagination from '../components/Pagination'

export default function Admin() {
  const [offset, setOffset] = useState(0)
  const users = useApi(`/users?limit=20&offset=${offset}`)
  const categories = useApi('/categories')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function categoryAction(name, remove) {
    if (remove && !window.confirm(`Delete category "${name}"?`)) return
    setError(''); setBusy(true)
    try {
      if (remove) await api.delete(`/categories/${encodeURIComponent(name)}`)
      else await api.post('/categories', { name })
      categories.reload()
    } catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <div className="stack"><div><p className="eyebrow">ADMINISTRATION</p><h1>Workspace settings</h1></div>
    <section className="card"><h2>Users & access</h2><p className="muted">Assign employees to a manager ID and vendors to a supplier ID. IDs are shown in user and supplier details.</p>
      <AsyncState {...users}>{users.data?.map(user => <UserEditor key={user.id} user={user} onSaved={users.reload} />)}
        <Pagination offset={offset} setOffset={setOffset} count={users.data?.length || 0} />
      </AsyncState>
    </section>
    <section className="card"><h2>Procurement categories</h2>{error && <p role="alert" className="error">{error}</p>}
      <form className="row" onSubmit={e => { e.preventDefault(); categoryAction(new FormData(e.currentTarget).get('name'), false) }}>
        <label>New category<input name="name" required maxLength={80} /></label><button disabled={busy}>Add category</button>
      </form><AsyncState {...categories}><ul className="stack" style={{ marginTop: '1rem' }}>{categories.data?.map(name => <li className="row between" key={name}>{name}<button className="secondary" disabled={busy} onClick={() => categoryAction(name, true)}>Delete</button></li>)}</ul></AsyncState>
    </section>
  </div>
}

function UserEditor({ user, onSaved }) {
  const [role, setRole] = useState(user.role)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true)
    const form = new FormData(event.currentTarget)
    try {
      await api.patch(`/users/${user.id}`, {
        role, is_active: form.get('is_active') === 'on',
        manager_id: role === 'employee' && form.get('manager_id') ? Number(form.get('manager_id')) : null,
        supplier_id: role === 'vendor' && form.get('supplier_id') ? Number(form.get('supplier_id')) : null,
      })
      onSaved()
    } catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <form className="card stack" style={{ marginBottom: '1rem' }} onSubmit={submit}>
    <strong>#{user.id} · {user.full_name} · {user.email}</strong>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="grid" style={{ marginTop: 0 }}><label>Role<select value={role} onChange={e => setRole(e.target.value)}>{['employee', 'manager', 'admin', 'vendor'].map(role => <option key={role}>{role}</option>)}</select></label>
      {role === 'employee' && <label>Manager ID<input name="manager_id" type="number" min="1" defaultValue={user.manager_id || ''} /></label>}
      {role === 'vendor' && <label>Supplier ID<input name="supplier_id" type="number" min="1" required defaultValue={user.supplier_id || ''} /></label>}
      <label className="row"><input style={{ width: 'auto' }} name="is_active" type="checkbox" defaultChecked={user.is_active} />Active account</label>
    </div><button disabled={busy}>{busy ? 'Saving…' : 'Save access'}</button>
  </form>
}
