import { Link, Route, Routes } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { AuthProvider, Protected } from './auth/AuthContext'
import Layout from './components/Layout'
import AuthPage from './pages/AuthPage'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Requests = lazy(() => import('./pages/Requests'))
const RequestForm = lazy(() => import('./pages/RequestForm'))
const EditRequest = lazy(() => import('./pages/RequestForm').then(module => ({ default: module.EditRequest })))
const RequestDetail = lazy(() => import('./pages/RequestDetail'))
const Suppliers = lazy(() => import('./pages/Suppliers'))
const SupplierDetail = lazy(() => import('./pages/Suppliers').then(module => ({ default: module.SupplierDetail })))
const Admin = lazy(() => import('./pages/Admin'))
const Orders = lazy(() => import('./pages/Orders'))
const OrderDetail = lazy(() => import('./pages/Orders').then(module => ({ default: module.OrderDetail })))
const Reports = lazy(() => import('./pages/Reports'))

export function Landing() {
  return <section className="hero">
    <p className="eyebrow">INTELLIGENT PROCUREMENT</p>
    <h1>Better purchasing.<br /><span>Every step of the way.</span></h1>
    <p>One workspace for requests, approvals, supplier decisions and delivery.
      Make confident choices with transparent, data-driven recommendations.</p>
    <Link className="button" to="/login">Enter your workspace</Link>
    <div className="feature-grid">
      {['Request with clarity', 'Choose with confidence', 'Track to delivery'].map((title, i) =>
        <article className="card" key={title}><span className="step">0{i + 1}</span><h2>{title}</h2></article>)}
    </div>
  </section>
}
export default function App() {
  return <AuthProvider><Layout><Suspense fallback={<p role="status">Loading page…</p>}><Routes><Route path="/" element={<Landing />} />
      <Route path="/login" element={<AuthPage />} />
      <Route path="/register" element={<AuthPage register />} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="/requests" element={<Protected roles={['employee', 'manager', 'admin']}><Requests /></Protected>} />
      <Route path="/requests/new" element={<Protected roles={['employee']}><RequestForm /></Protected>} />
      <Route path="/requests/:id/edit" element={<Protected roles={['employee']}><EditRequest /></Protected>} />
      <Route path="/requests/:id" element={<Protected roles={['employee', 'manager', 'admin']}><RequestDetail /></Protected>} />
      <Route path="/suppliers" element={<Protected roles={['employee', 'manager', 'admin']}><Suppliers /></Protected>} />
      <Route path="/suppliers/:id" element={<Protected roles={['employee', 'manager', 'admin']}><SupplierDetail /></Protected>} />
      <Route path="/admin" element={<Protected roles={['admin']}><Admin /></Protected>} />
      <Route path="/orders" element={<Protected><Orders /></Protected>} />
      <Route path="/orders/:id" element={<Protected><OrderDetail /></Protected>} />
      <Route path="/reports" element={<Protected roles={['manager', 'admin']}><Reports /></Protected>} />
      <Route path="*" element={<section className="card"><h1>Page not found</h1><Link to="/">Go home</Link></section>} />
    </Routes></Suspense></Layout></AuthProvider>
}
