import { Link, Route, Routes } from 'react-router-dom'
import { AuthProvider, Protected } from './auth/AuthContext'
import Layout from './components/Layout'
import AuthPage from './pages/AuthPage'
import Dashboard from './pages/Dashboard'
import Requests from './pages/Requests'
import RequestForm, { EditRequest } from './pages/RequestForm'
import RequestDetail from './pages/RequestDetail'
import Suppliers, { SupplierDetail } from './pages/Suppliers'
import Admin from './pages/Admin'
import Orders, { OrderDetail } from './pages/Orders'

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
  return <AuthProvider><Layout><Routes><Route path="/" element={<Landing />} />
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
      <Route path="*" element={<section className="card"><h1>Page not found</h1><Link to="/">Go home</Link></section>} />
    </Routes></Layout></AuthProvider>
}
