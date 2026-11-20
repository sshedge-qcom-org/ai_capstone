export default function Pagination({ offset, setOffset, count, limit = 20 }) {
  return <div className="pagination" aria-label="Pagination">
    <button className="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Previous</button>
    <span className="muted">Page {Math.floor(offset / limit) + 1}</span>
    <button className="secondary" disabled={count < limit} onClick={() => setOffset(offset + limit)}>Next</button>
  </div>
}
