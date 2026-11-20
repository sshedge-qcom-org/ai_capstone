"""Generate local configuration without shipping a shared signing secret."""

import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    raise SystemExit(".env already exists; refusing to overwrite it.")
template = (root / ".env.example").read_text()
target.write_text(template.replace("JWT_SECRET=\n", f"JWT_SECRET={secrets.token_urlsafe(48)}\n"))
target.chmod(0o600)
print("Created private local .env")
