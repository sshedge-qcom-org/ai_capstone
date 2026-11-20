import { Link, Route, Routes } from 'react-router-dom'

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
  return <>
    <header className="topbar"><Link className="brand" to="/">Procure<span>AI</span></Link>
      <span className="muted">Your procurement, connected.</span></header>
    <main id="main"><Routes><Route path="/" element={<Landing />} />
      <Route path="*" element={<section className="card"><h1>Page not found</h1><Link to="/">Go home</Link></section>} />
    </Routes></main>
  </>
}
