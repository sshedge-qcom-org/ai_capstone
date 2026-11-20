# AI Procurement Platform

Monorepo for a medium-sized company's procurement lifecycle, built with React,
FastAPI, SQLAlchemy, and SQLite.

## Delivery

| Phase | Deliverable | Status |
| --- | --- | --- |
| 0 | Architecture, data model, API and UX contracts | Complete |
| 1 | Runnable monorepo, migrations, health and landing page | Complete |
| 2 | Authentication, rotating refresh tokens, role guards | Complete |
| 3 | Role-scoped dashboard, KPI cards, trends and demo data | Complete |
| 4 | Request CRUD, team review, revision and approval history | Complete |
| 5 | Supplier directory, admin CRUD, user/category administration | Complete |
| 6 | Explainable top-three weighted supplier ranking | Complete |
| 7 | Order creation, vendor fulfilment, immutable value and history | Complete |
| 8 | Threaded comments, replies, edits and safe deletion | Complete |
| 9 | Scoped reports, visualizations and safe CSV export | Complete |
| 10 | Production hardening, integration/browser verification, release docs | Complete |

Start with the [architecture](docs/architecture.md), [schema](docs/schema.md),
[API contract](docs/api.md), [page map](docs/frontend.md), and
[user journeys](docs/journeys.md). The [delivery plan](docs/delivery.md) defines
verification gates and operational boundaries.

## Local setup

Requires Python 3.11+ and Node.js 22+.

```sh
python3 scripts/configure.py
python3 -m venv .venv
.venv/bin/pip install -e './backend[dev]'
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/uvicorn app.main:app --reload
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. API health: http://127.0.0.1:8000/api/v1/health.
Swagger: http://127.0.0.1:8000/docs. Environment values load from the root `.env`;
relative SQLite paths resolve from the backend working directory.

## Verification

```sh
.venv/bin/python scripts/verify.py
cd frontend && npx playwright install chromium && cd ..
.venv/bin/python scripts/e2e.py
```

The first command checks lint/format, Python compilation, migration
upgrade/downgrade/model parity on a temporary database, all API tests, frontend
build/lint/tests and dependency advisories. The second verification script starts
isolated test servers, seeds a temporary database with random credentials, runs
real Chromium workflows and WCAG automated checks, then stops the servers.
Neither verification script modifies the local development database.
GitHub Actions runs the same gates.
Add `--postman` to the E2E command to execute all 45 Postman requests with Newman.

For reproducible Python dependencies, use
`.venv/bin/pip install -r backend/requirements.lock` before installing the backend.
The lock records the verified Python 3.14 environment. Python 3.11+ is the declared
minimum; other minors require their own runtime verification.

## Features and phase notes

Phase 1: migration, health test, frontend build/lint and landing test pass.
Phase 2 adds login/registration, in-memory access tokens, HttpOnly rotating refresh
cookies, role authorization and user administration APIs. Public registration
cannot choose a privileged role. Administrators assign an employee's manager.

To create local test users, set `DEMO_PASSWORD` to the requested local demo password
and run `cd backend && ../.venv/bin/python -m app.seed`. Accounts:
`admin@company.com`, `manager@company.com`, `employee@company.com`,
`vendor@company.com`. The seed refuses to run outside development and does not
overwrite existing passwords. Never use these accounts in production.

Phase 3: dashboard KPIs, delivered monthly spending, approval breakdown and top
suppliers use scoped SQL aggregates. The explicit seed includes 30 suppliers,
30 requests and 20 orders across several months. Re-run migrations and seed after
upgrading. Vendors see only their linked supplier's orders.

Phase 4: employees create and edit pending/revision requests; managers review
their team's requests; admins see all. Rejection/revision require reasons.
Approved/rejected/ordered requests cannot be edited. Conditional updates prevent
concurrent workflow overwrites. Lists have server-side search, filters and paging.

Phase 5: searchable and category-filtered directory, supplier details, admin
create/update/delete, category configuration and user/team/vendor assignment UI.
Thirty seed suppliers cover five categories. Referenced suppliers/categories
cannot be deleted; suppliers with historical orders cannot switch category.

Phase 6: approved requests show at most three matching suppliers, deterministic
scores and factor explanations. Price/rating/reliability normalize to their
documented scales; delivery uses `1 / (1 + days / 7)`. This is a transparent
weighted ranking engine, not a trained ML model. Tests cover exact weights,
ranking, stable ties, category matching, empty results and authorization.

Phase 7: managers/admins select a matching supplier and create exactly one order
for an approved request. The order snapshots its approved estimated total.
Assigned vendors/admins advance Created → Processing → Shipped → Delivered.
Transitions are audited and delivery updates dashboard spending. Order lists and
details are scoped to employee ownership, manager team or vendor supplier.

Phase 8: request participants can discuss, reply and edit their own comments.
Admins may moderate deletion; tombstones preserve descendants. Parent IDs cannot
cross requests. Roots and direct replies are independently paginated, with replies
loaded on expansion. Eight reply levels keep nested discussions usable.

Phase 9: managers/admins can filter reports by UTC date range and export spending
by category, supplier performance, monthly activity and approval turnaround.
CSV files neutralize spreadsheet formulas. Financial reports reconcile with
dashboard delivered spending. Turnaround measures creation to the first final
approval/rejection, excluding revision events.

Phase 10 adds bounded authentication throttling, safe validation/database error
responses, request IDs, refresh revocation on access changes, comment edit conflict
checks, an error boundary, route-level code splitting, accessible chart tables,
automated browser workflows, a locked environment and CI. The generated
[Postman collection](postman/procurement.postman_collection.json) covers every API
operation and contains no credentials.

Verified locally: 25 Pytest cases, the frontend landing test, two Chromium
journeys, desktop/mobile automated accessibility checks, and 45 Postman requests
with 46 assertions. All pass. Migration round-trips and lint/build checks pass;
the frontend dependency audit reports zero advisories.

## Documentation and operations

- [Architecture and ranking design](docs/architecture.md)
- [ER diagram and schema](docs/schema.md)
- [API contracts](docs/api.md) and live Swagger at `/docs`
- [Setup, production deployment, backup and restore](docs/setup.md)
- [Role-based user guide](docs/user-guide.md)
- [Contribution guide](CONTRIBUTING.md)
- [Postman lifecycle instructions](postman/README.md)

Release: `v1.0.0`. All eleven phase commits are local; no remote push is performed.

This is a working single-instance release. Before company rollout, configure TLS,
reverse-proxy limits, monitoring and encrypted backups; complete load testing and
organization-specific security/operational review. SQLite is not a horizontally
scaled database. SSO/MFA, password recovery, payments and negotiated supplier
quotes are outside this release's scope.

Next step: follow the deployment guide and complete the operational acceptance
checklist in your staging environment.