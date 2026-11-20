# Monorepo structure

```text
ai-procurement-platform/
  backend/
    app/
      main.py
      config.py
      database.py
      models.py
      schemas.py
      security.py
      dependencies.py
      repositories/
      services/
      api/
      seed.py
    migrations/
      versions/
    tests/
    alembic.ini
    pyproject.toml
  frontend/
    src/
      api/
      auth/
      components/
      pages/
      App.jsx
      main.jsx
      index.css
    package.json
    vite.config.js
    eslint.config.js
  docs/
  postman/
  scripts/
  .env.example
  .gitignore
  README.md
  CONTRIBUTING.md
```

Keep modules small and purpose-driven. Repositories perform database access,
services implement business rules, routers translate HTTP, and pages compose
shared accessible components. Avoid generic abstractions without actual reuse.
Migrations, not implicit table creation on application startup, define production
schema changes. Test databases may build metadata for isolated fixtures.
