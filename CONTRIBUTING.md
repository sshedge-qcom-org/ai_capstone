# Contributing

1. Follow [local setup](README.md#local-setup). Never commit `.env`, databases,
   access tokens, browser traces, or account passwords.
2. Keep HTTP handling in routers, policy/workflows in services and queries in
   repositories. Enforce role and resource authorization on the server.
3. Use Pydantic DTOs with explicit writable fields; never accept an ORM model
   directly from clients. Use decimal money, UTC timestamps and audited transitions.
4. Schema changes require an Alembic migration. Inspect generated migrations:
   SQLite cannot add standalone foreign key constraints. Test both upgrade and
   downgrade on a disposable database.
5. Add focused regression tests for changed behavior. Run
   `.venv/bin/python scripts/verify.py`, then
   `.venv/bin/python scripts/e2e.py` for UI/workflow changes.
6. Update API/architecture/user documentation when contracts or workflows change.
7. Keep commits phase-scoped. Avoid unrelated formatting or dependencies.

## Test environments

Pytest creates isolated temporary databases and never seeds application startup.
The E2E runner creates a temporary database and random test credentials, owns its
servers, and cleans them up. Running `npm run test:e2e` directly instead targets
the local demo database and needs `DEMO_PASSWORD`; use only a disposable deployment.
The Postman collection also intentionally mutates its target demo database and
vendor assignment. Do not retain traces containing credentials outside local development.

## Pull requests

Include the user-visible change, migration implications, validation commands and
results. Report remaining deployment assumptions honestly. No TODO placeholders,
fake successful responses or hardcoded frontend procurement data.
