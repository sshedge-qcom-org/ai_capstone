"""Generate private staging configuration without modifying development settings."""

import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
directory = root / "deploy/runtime"
directory.mkdir(mode=0o700, parents=True, exist_ok=True)
target = directory / "staging.env"
content = (
    "APP_NAME=AI Procurement Platform - Staging\n"
    "ENVIRONMENT=production\n"
    "DATABASE_URL=sqlite:////data/procurement.db\n"
    f"JWT_SECRET={secrets.token_urlsafe(48)}\n"
    "COOKIE_SECURE=true\n"
    'CORS_ORIGINS=["https://localhost:8443"]\n'
    "AUTH_RATE_LIMIT=60\n"
)
try:
    descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
except FileExistsError as exc:
    raise SystemExit(
        "Staging configuration already exists; refusing to rotate its secret"
    ) from exc
with os.fdopen(descriptor, "w") as stream:
    stream.write(content)
print("Created private deploy/runtime/staging.env; no demo users will be seeded.")
