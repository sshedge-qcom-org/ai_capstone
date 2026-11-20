import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, errorMessage } from '../api/client'
import { AsyncState, useApi } from '../components/Async'

export function EditRequest() {
  const { id } = useParams()
  const state = useApi(`/requests/${id}`)
  return <AsyncState {...state}>{state.data && <RequestForm initial={state.data} />}</AsyncState>
}

export default function RequestForm({ initial }) {
  const categories = useApi('/categories')
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event) {
    event.preventDefault()
    setError(''); setBusy(true)
    const data = Object.fromEntries(new FormData(event.currentTarget))
    data.quantity = Number(data.quantity)
    try {
      const response = initial ? await api.patch(`/requests/${initial.id}`, data) : await api.post('/requests', data)
      navigate(`/requests/${response.data.id}`)
    } catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <><Link to="/requests">← Purchase requests</Link><h1 style={{ marginTop: '1rem' }}>{initial ? 'Edit & resubmit request' : 'Create purchase request'}</h1>
    <AsyncState {...categories}><section className="card">
      {error && <p className="error" role="alert">{error}</p>}
      <form className="form" onSubmit={submit}>
        <label>Item name<input name="title" required maxLength={120} defaultValue={initial?.title} /></label>
        <label>Category<select name="category" required defaultValue={initial?.category || ''}><option value="" disabled>Choose category</option>
          {categories.data?.map(c => <option key={c}>{c}</option>)}</select></label>
        <div className="grid" style={{ marginTop: 0 }}>
          <label>Quantity<input name="quantity" type="number" required min="1" max="1000000" step="1" defaultValue={initial?.quantity || 1} /></label>
          <label>Estimated total budget (USD)<input name="estimated_budget" type="number" min=".01" max="9999999999.99" step=".01" required defaultValue={initial?.estimated_budget} /></label>
        </div>
        <label>Target delivery date<input name="target_delivery_date" type="date" min={new Date().toISOString().slice(0, 10)} required defaultValue={initial?.target_delivery_date} /></label>
        <label>Justification<textarea name="description" required minLength={10} maxLength={5000} defaultValue={initial?.description} /></label>
        <button disabled={busy || !categories.data?.length}>{busy ? 'Saving…' : initial ? 'Save & submit for approval' : 'Submit for approval'}</button>
        {!categories.data?.length && <p role="alert">Ask an administrator to configure a category before submitting.</p>}
      </form>
    </section></AsyncState>
  </>
}
