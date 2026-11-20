"""Run deterministic local checks without starting or modifying the demo database."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
python = Path(sys.executable)


def run(args: list[str], cwd: Path = root, env: dict[str, str] | None = None):
    print(f"\nChecking: {' '.join(args)}", flush=True)
    subprocess.run(args, cwd=cwd, env=env, check=True)


run([str(python), "-m", "ruff", "check", "backend", "scripts"])
run([str(python), "-m", "ruff", "format", "--check", "backend", "scripts"])
run([str(python), "-m", "compileall", "-q", "backend/app"])
with tempfile.TemporaryDirectory(prefix="procureai-verification-") as directory:
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{directory}/migration.db"}
    for args in (
        ["upgrade", "head"],
        ["check"],
        ["downgrade", "base"],
        ["upgrade", "head"],
    ):
        run([str(python), "-m", "alembic", *args], root / "backend", env)
run([str(python), "-m", "pytest", "-q"], root / "backend")
for command in (
    ["npm", "run", "build"],
    ["npm", "run", "lint"],
    ["npm", "test"],
    ["npm", "audit"],
):
    run(command, root / "frontend")
run(["git", "diff", "--check"])
print(
    "\nAll deterministic checks passed. Run browser E2E separately against local demo servers."
)
