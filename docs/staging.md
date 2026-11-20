# Local HTTPS staging

This is an isolated, production-mode deployment on this computer, not a cloud
deployment. It uses Docker Compose, a built React frontend served by Caddy, a
single non-root FastAPI worker, and its own persistent SQLite volume.
The only published port is `127.0.0.1:8443`; the development app on port 5173 and
its database/configuration are unchanged.

## Start

Requires Docker Desktop/Engine with Compose v2+, plus the development verification
dependencies and Chromium described in the README.

```sh
.venv/bin/python scripts/configure_staging.py
docker compose -f deploy/compose.yml build
docker compose -f deploy/compose.yml up -d --wait --wait-timeout 120
.venv/bin/python scripts/verify_staging.py
```

The configuration generator creates a new random JWT secret in
`deploy/runtime/staging.env` with mode 0600, refuses to overwrite an existing
file, and never modifies `.env`. The runtime directory is private and excluded
from Git and Docker build contexts. Restrict Docker socket access to trusted
operators: container administrators can inspect container environments.

The backend runs migrations before startup. No demo users, suppliers, requests,
or orders are seeded. Logs rotate at 10 MB per file, with three files per service.
Containers use a read-only root filesystem, bounded resources, dropped
capabilities and `no-new-privileges`. Writable data is limited to named volumes
and bounded temporary filesystems.

## Local certificate trust

Open **https://localhost:8443**. Caddy generates a private local certificate
authority; it is deliberately not installed into your computer's trust store
automatically. The verification script copies only its public CA certificate to
`deploy/runtime/staging-ca.crt` and verifies the actual TLS chain with it.

You can inspect/verify without changing global trust:

```sh
curl --cacert deploy/runtime/staging-ca.crt https://localhost:8443/api/v1/health
```

For browser use, inspect that certificate and explicitly trust it using your
operating system/browser certificate UI. On macOS, import the public certificate
into your login keychain using Keychain Access and review its trust settings.
This is an operator decision; do not bypass certificate warnings for a remote
site or copy the CA's private key out of the Caddy volume.

The automated Chromium staging test permits the local, otherwise-untrusted CA
only in its isolated test context. Independent HTTP acceptance verifies the TLS
certificate normally; application code never disables TLS verification.

## First administrator

The initial deployment intentionally has no privileged account. Run this
interactively, using your intended administrator email/name and a new password:

```sh
docker compose -f deploy/compose.yml exec backend \
  python -m app.manage create-admin \
  --email admin@company.com --full-name "Procurement Administrator"
```

The command prompts securely twice. Do not reuse the development demo password.
Sign in, configure categories and suppliers, then assign registered employees
their managers and registered vendors their suppliers. There are no staging
credentials stored in source or in the acceptance report.

## Operational acceptance

`.venv/bin/python scripts/verify_staging.py` targets only
`https://localhost:8443` and the Compose project declared in this repository.
It checks:

- CA-verified HTTPS, security headers, SPA deep links and genuine missing-asset 404s.
- Internal API docs are not published through the proxy.
- Registration/login, JWT authorization, Secure/HttpOnly/SameSite refresh cookies,
  rotation, origin validation and logout.
- A real browser against the built production frontend, including reload/session
  restoration, logout and no observed CSP violations.
- Schema parity and a consistent online backup.
- A restored copy of that backup running the real API on an internal ephemeral
  socket, with readiness, login and identity verification.
- Authentication throttling, including attempts to spoof forwarded client IPs.
- Data and signing-key persistence across an actual backend restart.
- A bounded 100-request probe, concurrency five, against landing/health endpoints;
  zero errors and p95 below 1000 ms are the local smoke acceptance gates.

The script creates a randomly credentialed, uniquely identified employee only
for verification. It removes that exact identity and its refresh sessions, the
temporary backup and restore script when finished. It refuses to delete an
identity that changed or acquired procurement history. Restored test databases
are disposable and never replace the live database.

The restore drill uses the container's 32 MB temporary filesystem, so it is a
small-fixture startup/recovery check, not a large-database recovery benchmark.
For a real larger dataset, follow the full restore procedure in the setup guide.

The latest non-sensitive report is saved to `deploy/runtime/acceptance.json`.
The local acceptance run on 2026-11-20 passed all checks, including a real restore
and browser session. Its latest 100-request probe had zero errors and a 7.23 ms p95.
This is not a throughput guarantee, company SLA, or authenticated-workload
capacity test.

## Operations and shutdown

```sh
docker compose -f deploy/compose.yml ps
docker compose -f deploy/compose.yml logs --tail 100 backend web
docker compose -f deploy/compose.yml exec backend python -m app.manage prune-sessions
docker compose -f deploy/compose.yml stop
docker compose -f deploy/compose.yml start --wait
```

Stopping/restarting preserves database and certificate volumes. Do not remove
volumes to fix an application error. Keep signing keys and the database together
as part of a deliberate recovery/rotation plan.

For a real backup, choose a new filename and copy it to a protected location:

```sh
docker compose -f deploy/compose.yml exec backend \
  python -m app.manage backup --output /data/backups/operator-backup.db
docker compose -f deploy/compose.yml cp \
  backend:/data/backups/operator-backup.db deploy/runtime/operator-backup.db
```

Move operator backups to encrypted off-host storage according to company policy;
the acceptance drill's disposable snapshot is not a backup retention system.

## Gates before external rollout

The following are not completed by a local deployment:

1. Select the actual host, domain, DNS, access policy and infrastructure owner.
2. Replace local internal TLS with certificates for that domain, update the Caddy
   site/CORS allowlist and bind only the intended interface. Enable HSTS only after
   validating the real HTTPS deployment.
3. Configure company monitoring/alerting, scheduled encrypted backup retention,
   a tested disaster-recovery owner, and authenticated-workload load tests.
4. Complete organizational security review, identity/account recovery policy and
   user acceptance. SSO/MFA and password recovery remain outside v1.0.0.
5. Promote a reviewed immutable image digest through your release process.

Nothing is pushed to GitHub or deployed to an external provider by these commands.
