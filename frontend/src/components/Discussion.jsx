import { useState } from 'react'
import { api, errorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { AsyncState, date, useApi } from './Async'
import Pagination from './Pagination'

export default function Discussion({ requestId }) {
  const [version, setVersion] = useState(0)
  return <section className="card"><h2>Discussion</h2><p className="muted">Collaborate with your procurement team. Replies support up to eight levels.</p>
    <CommentForm requestId={requestId} onSaved={() => setVersion(v => v + 1)} />
    <Thread key={version} requestId={requestId} depth={0} />
  </section>
}

function Thread({ requestId, parentId, depth }) {
  const [offset, setOffset] = useState(0)
  const state = useApi(`/requests/${requestId}/comments?limit=20&offset=${offset}${parentId ? `&parent_id=${parentId}` : ''}`)
  return <AsyncState {...state}><div className="stack" style={{ marginTop: '1rem' }}>
    {state.data?.map(comment => <CommentNode key={comment.id} comment={comment} requestId={requestId} depth={depth} reload={state.reload} />)}
    {state.data?.length === 0 && !parentId && <p>No comments yet. Start the conversation.</p>}
    {(offset > 0 || state.data?.length === 20) && <Pagination offset={offset} setOffset={setOffset} count={state.data?.length || 0} />}
  </div></AsyncState>
}

function CommentNode({ comment, requestId, depth, reload }) {
  const { user } = useAuth()
  const [mode, setMode] = useState('')
  const [expanded, setExpanded] = useState(false)
  const [version, setVersion] = useState(0)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function remove() {
    if (!window.confirm('Delete this comment? Replies will be preserved.')) return
    setBusy(true); setError('')
    try { await api.delete(`/comments/${comment.id}`); reload() }
    catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  function saved() {
    setMode(''); setExpanded(true); setVersion(v => v + 1); reload()
  }
  return <article className="comment">
    <div className="row between"><strong>{comment.author_name}</strong><span className="muted">{date(comment.created_at)}</span></div>
    {error && <p className="error" role="alert">{error}</p>}
    <p style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{comment.content}</p>
    <div className="row">
      {depth < 8 && <button className="secondary" onClick={() => setMode(mode === 'reply' ? '' : 'reply')}>Reply</button>}
      {!comment.is_deleted && user.id === comment.user_id && <button className="secondary" onClick={() => setMode(mode === 'edit' ? '' : 'edit')}>Edit</button>}
      {!comment.is_deleted && (user.id === comment.user_id || user.role === 'admin') && <button className="secondary" disabled={busy} onClick={remove}>Delete</button>}
      {comment.reply_count > 0 && <button className="secondary" onClick={() => setExpanded(!expanded)}>{expanded ? 'Hide' : 'Show'} replies ({comment.reply_count})</button>}
    </div>
    {mode && <CommentForm requestId={requestId} parentId={mode === 'reply' ? comment.id : undefined} editing={mode === 'edit' ? comment : undefined} onSaved={saved} />}
    {expanded && <Thread key={version} requestId={requestId} parentId={comment.id} depth={depth + 1} />}
  </article>
}

function CommentForm({ requestId, parentId, editing, onSaved }) {
  const [content, setContent] = useState(editing?.content || '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      if (editing) await api.patch(`/comments/${editing.id}`, { content })
      else await api.post(`/requests/${requestId}/comments`, { content, parent_comment_id: parentId || null })
      setContent(''); onSaved()
    } catch (error) { setError(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return <form className="form" style={{ marginTop: '1rem' }} onSubmit={submit}>
    {error && <p role="alert" className="error">{error}</p>}
    <label>{editing ? 'Edit comment' : parentId ? 'Your reply' : 'New comment'}<textarea value={content} maxLength={5000} required onChange={e => setContent(e.target.value)} /></label>
    <button disabled={busy || !content.trim()}>{busy ? 'Saving…' : editing ? 'Save comment' : parentId ? 'Post reply' : 'Post comment'}</button>
  </form>
}
