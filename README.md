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
| 6-10 | Recommendation engine through production hardening | Planned |

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
.venv/bin/ruff check backend scripts
.venv/bin/python -m compileall -q backend/app
cd backend && ../.venv/bin/pytest -q
cd ../frontend && npm run build && npm run lint && npm test
```

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

Next: explained top-three weighted supplier recommendations.