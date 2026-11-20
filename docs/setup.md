# Setup and deployment

## Development

From the repository root, follow the README setup. Run migrations from `backend/`
before the API. Configuration loads from the root `.env`; do not overwrite an
existing configuration with `scripts/configure.py`.

VS Code defaults to the repository's `.venv` and includes `backend/` in analysis
paths. If the editor already has another interpreter selected, use **Python:
Select Interpreter** to choose this project's `.venv`; installing into the terminal
environment does not change an existing editor selection.

The demo seed needs an explicitly supplied `DEMO_PASSWORD`. Set it locally to
the requested demo password, then run `python -m app.seed` using the virtual
environment from `backend/`. It creates four role accounts, 30 suppliers,
30 requests, 20 orders and their histories. It preserves existing account
passwords and refuses to run in production. Do not expose demo accounts publicly.

Vite proxies `/api` to port 8000, so cookies are same-origin. Use
http://localhost:5173, matching the CORS allowlist. If you use another host/port,
update `CORS_ORIGINS` and restart the API. A direct cross-origin deployment must
still be same-site for the Strict refresh cookie; same-origin proxying is preferred.

## Production single-instance deployment

For a ready-to-run, isolated local deployment with production settings and
CA-verified HTTPS acceptance tests, follow the [staging guide](staging.md).
It does not replace the external rollout decisions below.

1. Provision Python 3.11+ and Node 22+. Install the locked Python dependencies
   using `pip install -r backend/requirements.lock` and `pip install ./backend`.
   The lock records the verified Python 3.14 environment; retest dependency
   resolution before deploying a different supported Python minor version.
2. Create a private environment file or inject variables using the process
   manager. Generate a unique random JWT secret (at least 32 characters), set
   `ENVIRONMENT=production`, `COOKIE_SECURE=true`, an explicit HTTPS
   `CORS_ORIGINS` JSON array, and an absolute `DATABASE_URL` on a local disk.
   Never use the development secret or seed accounts.
3. From `backend/`, run `alembic upgrade head`. Create the first admin using
   `python -m app.manage create-admin --email admin@your-domain.example --full-name "Procurement Admin"`.
   The command securely prompts twice and validates the password.
4. Run `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1`.
   Use a supervised service with automatic restart. Do not use `--reload`.
5. Run `npm ci && npm run build` in `frontend/`. Serve `dist/` behind a TLS
   reverse proxy with SPA fallback to `index.html`; proxy `/api/` to the backend.
   Vite's development proxy is not a production server.
6. Configure proxy body-size/time limits and authentication rate limits. The
   application's bounded, per-IP 60/minute auth throttle is process-local and
   resets on restart. Trust forwarded client IPs only from your reverse proxy.
   Do not run multiple workers against this SQLite deployment.
7. Set static response security headers: CSP restricting scripts/styles/connects
   to your application (chart layout uses inline styles), frame-ancestors none,
   nosniff, and HSTS after confirming TLS. Deny framing on the API. Restrict
   `/docs` and `/openapi.json` at the proxy if they are internal-only.
8. Configure monitoring for health, error rates, disk usage and latency. Logs
   include method/path/status and a generated request ID, not request bodies or
   authorization tokens. Unexpected failures are generic to clients.

## Backup, restore and maintenance

From `backend/`, run `python -m app.manage backup --output /safe/new-backup.db`.
It refuses to overwrite a path, uses SQLite's online backup API and checks
integrity. Encrypt backups, restrict access and store copies off-host.

To restore: stop the API, preserve the current database and its WAL/SHM sidecars
as a recovery set, restore the verified backup to a new path, point
`DATABASE_URL` at that path, run migrations and start the API. Test readiness,
sign-in and representative requests. Practice restores before rollout; never
copy just an active main database file while writes are running.

Schedule `python -m app.manage prune-sessions` daily to remove expired sessions.
Keep the JWT secret stable across restarts; rotate it deliberately to invalidate
all outstanding JWTs. Logout revokes refresh; already-issued access tokens expire
within 15 minutes. Deactivated users are rejected immediately on every API call.

## Capacity and rollout boundaries

This release is a working single-instance application, not an externally
certified production service. Complete organization-specific threat review,
load tests, disaster recovery exercises, SSO/account recovery policy and
operational acceptance before rollout. SMTP, password recovery, MFA, ERP/payment
integrations and negotiated supplier quotes are not implemented. Move to a
server database and shared rate limiter before horizontal scaling.
