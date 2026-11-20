import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, errorMessage } from '../api/client'
import { AsyncState, money, useApi } from '../components/Async'

const reports = [
  { key: 'spending_by_category', title: 'Spending by category', name: 'category', value: 'amount', columns: ['category', 'amount', 'orders'] },
  { key: 'supplier_performance', title: 'Supplier performance', name: 'supplier', value: 'delivered_value', columns: ['supplier', 'rating', 'reliability_score', 'total_orders', 'delivered_orders', 'delivered_value', 'average_actual_delivery_days'] },
  { key: 'monthly_trends', title: 'Monthly procurement trends', name: 'month', value: 'amount', columns: ['month', 'requests', 'amount', 'delivered_orders'] },
  { key: 'approval_turnaround', title: 'Approval turnaround time', name: 'category', value: 'average_hours', columns: ['category', 'decided_requests', 'average_hours'] },
]
const label = key => key.replaceAll('_', ' ')
const format = (key, value) => value === null ? '—' : ['amount', 'delivered_value'].includes(key) ? money(value) : typeof value === 'number' && !Number.isInteger(value) ? value.toFixed(2) : value

export default function Reports() {
  const [query, setQuery] = useState('')
  const state = useApi(`/reports${query ? `?${query}` : ''}`)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  async function download(key) {
    setError(''); setBusy(key)
    let url
    try {
      const { data } = await api.get(`/reports/export?report=${key}${query ? `&${query}` : ''}`, { responseType: 'blob' })
      url = URL.createObjectURL(data)
      const anchor = document.createElement('a')
      anchor.href = url; anchor.download = `${key}.csv`; anchor.click()
    } catch (error) {
      if (error.response?.data instanceof Blob) {
        const text = await error.response.data.text()
        try { error.response.data = JSON.parse(text) } catch { error.response.data = { detail: 'Export failed. Please try again.' } }
      }
      setError(errorMessage(error))
    } finally { if (url) URL.revokeObjectURL(url); setBusy('') }
  }
  return <div className="stack"><div><p className="eyebrow">PROCUREMENT INTELLIGENCE</p><h1>Reports & analytics</h1>
    <p className="muted">Financial figures count delivered orders, valued at their approved estimates. Dates use UTC.</p></div>
    <form className="card row" onSubmit={event => {
      event.preventDefault()
      const data = Object.fromEntries(new FormData(event.currentTarget))
      setQuery(new URLSearchParams(Object.entries(data).filter(([, value]) => value)).toString())
    }}>
      <label>From<input type="date" name="since" /></label><label>Through<input type="date" name="until" /></label><button>Apply dates</button>
    </form>
    {error && <p role="alert" className="error">{error}</p>}
    <AsyncState {...state}>{state.data && reports.map(report => {
      const rows = state.data[report.key]
      const chartData = rows.map(row => ({ ...row, [report.value]: Number(row[report.value]) }))
      return <section className="card" key={report.key}><div className="row between"><h2>{report.title}</h2><button className="secondary" disabled={Boolean(busy)} onClick={() => download(report.key)}>{busy === report.key ? 'Exporting…' : 'Export CSV'}</button></div>
        {rows.length ? <>
          <div className="chart" role="img" aria-label={`${report.title} chart; values are in the table below`}><ResponsiveContainer>
            {report.key === 'monthly_trends' ? <LineChart data={chartData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey={report.name} /><YAxis width={65} /><Tooltip /><Line dataKey={report.value} stroke="#146c67" strokeWidth={3} /></LineChart>
              : <BarChart data={chartData}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey={report.name} hide={report.key === 'supplier_performance'} /><YAxis width={65} /><Tooltip /><Bar dataKey={report.value} fill="#146c67" radius={[4, 4, 0, 0]} /></BarChart>}
          </ResponsiveContainer></div>
          <div className="table-wrap"><table><caption className="sr-only">{report.title} data</caption><thead><tr>{report.columns.map(key => <th key={key}>{label(key)}</th>)}</tr></thead>
            <tbody>{rows.map((row, i) => <tr key={i}>{report.columns.map(key => <td key={key}>{format(key, row[key])}</td>)}</tr>)}</tbody></table></div>
        </> : <p>No data in this reporting period.</p>}
      </section>
    })}</AsyncState>
  </div>
}
