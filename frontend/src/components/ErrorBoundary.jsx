import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(error, info) { console.error('Workspace rendering failed', error, info.componentStack) }
  render() {
    if (this.state.failed) return <main className="card" role="alert">
      <h1>Something went wrong</h1><p>The workspace could not be displayed. Reload to restore your session and try again.</p>
      <button onClick={() => window.location.reload()}>Reload workspace</button>
    </main>
    return this.props.children
  }
}
