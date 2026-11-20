import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useAuth } from '../auth/AuthContext'
import { AsyncState, money, useApi } from '../components/Async'

const colors = ['#146c67', '#d2a245', '#557b9b', '#a65361', '#9081ac']

export default function Dashboard() {
  const state = useApi('/dashboard')
  const { user } = useAuth()
  const data = state.data
  const vendor = user.role === 'vendor'
  return <AsyncState {...state}>{data && <>
    <div className="row between"><div><p className="eyebrow">YOUR PROCUREMENT WORKSPACE</p>
      <h1>Overview</h1><p className="muted">{vendor ? 'Assigned supplier orders and fulfilment.' : user.role === 'admin' ? 'Company-wide purchasing at a glance.' : 'Your procurement activity, in one place.'}</p></div>
      {user.role === 'employee' && <Link className="button" to="/requests/new">+ New request</Link>}
      {vendor && <Link className="button" to="/orders">View assigned orders</Link>}
    </div>
    <div className="grid">
      {(vendor ? [['Assigned orders', data.approved_orders], ['Delivered value', money(data.procurement_spend)]] : [
        ['Total requests', data.total_requests], ['Pending approvals', data.pending_approvals],
        ['Approved orders', data.approved_orders], ['Procurement spend', money(data.procurement_spend)],
        ['Active suppliers', data.total_suppliers],
      ]).map(([label, value]) => <article className="card" key={label}><p className="muted">{label}</p><div className="kpi">{value}</div></article>)}
    </div>
    <div className="grid">
      <section className="card"><h2>Monthly delivered spending</h2>
        {data.monthly_spending.length ? <div className="chart" role="img" aria-label="Monthly delivered spending chart"><ResponsiveContainer><LineChart data={data.monthly_spending.map(row => ({ ...row, amount: Number(row.amount) }))}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="month" /><YAxis width={65} />
          <Tooltip formatter={money} /><Line type="monotone" dataKey="amount" stroke="#146c67" strokeWidth={3} />
        </LineChart></ResponsiveContainer></div> : <p>No delivered orders yet.</p>}
        <details><summary>View spending data</summary><ul>{data.monthly_spending.map(row => <li key={row.month}>{row.month}: {money(row.amount)}</li>)}</ul></details>
      </section>
      {!vendor && <section className="card"><h2>Request approval status</h2>
        {data.approval_status.length ? <div className="chart" role="img" aria-label="Request approval status chart"><ResponsiveContainer><PieChart>
          <Pie data={data.approval_status} nameKey="status" dataKey="count" innerRadius={65} outerRadius={100}>
            {data.approval_status.map((row, i) => <Cell key={row.status} fill={colors[i % colors.length]} />)}
          </Pie><Tooltip />
        </PieChart></ResponsiveContainer></div> : <p>No requests yet.</p>}
        <div className="row">{data.approval_status.map(row => <span className="badge" key={row.status}>{row.status}: {row.count}</span>)}</div>
      </section>}
    </div>
    {!vendor && <section className="card" style={{ marginTop: '1.5rem' }}><h2>Top suppliers by delivered value</h2>
      {data.top_suppliers.length ? <><div className="chart" role="img" aria-label="Top suppliers by delivered order value"><ResponsiveContainer><BarChart data={data.top_suppliers.map(row => ({ ...row, amount: Number(row.amount) }))}>
        <XAxis dataKey="supplier" hide /><YAxis width={65} /><Tooltip formatter={money} /><Bar dataKey="amount" fill="#146c67" radius={[4, 4, 0, 0]} />
      </BarChart></ResponsiveContainer></div><ul>{data.top_suppliers.map(row => <li key={row.supplier}>{row.supplier}: {money(row.amount)}</li>)}</ul></> : <p>Supplier rankings appear after delivery.</p>}
    </section>}
  </>}</AsyncState>
}
