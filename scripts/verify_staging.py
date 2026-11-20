"""Exercise only this repository's loopback Docker staging deployment."""

import asyncio
import json
import math
import os
import secrets
import ssl
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "deploy/runtime"
COMPOSE = ["docker", "compose", "-f", str(ROOT / "deploy/compose.yml")]
BASE = "https://localhost:8443"


def compose(*args: str, payload: str | None = None) -> str:
    try:
        result = subprocess.run(
            [*COMPOSE, *args],
            cwd=ROOT,
            input=payload,
            text=True,
            capture_output=True,
            check=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stderr, file=sys.stderr)
        raise
    return result.stdout.strip()


def require(condition: bool, message: str):
    if not condition:
        raise RuntimeError(message)


def wait_ready(client: httpx.Client):
    for _ in range(100):
        try:
            response = client.get("/api/v1/health")
            if response.status_code == 200:
                return
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
            pass
        time.sleep(0.1)
    raise RuntimeError("HTTPS staging did not become ready")


async def load_probe(context: ssl.SSLContext) -> dict:
    semaphore = asyncio.Semaphore(5)
    async with httpx.AsyncClient(base_url=BASE, verify=context, timeout=10) as client:

        async def sample(index: int) -> float:
            async with semaphore:
                start = time.perf_counter()
                response = await client.get("/api/v1/health" if index % 2 else "/")
                response.raise_for_status()
                return (time.perf_counter() - start) * 1000

        durations = sorted(
            await asyncio.gather(*(sample(index) for index in range(100)))
        )
    p95 = durations[math.ceil(len(durations) * 0.95) - 1]
    require(
        p95 < 1000,
        f"Local staging latency exceeded the 1000 ms probe gate: {p95:.1f} ms",
    )
    return {"requests": 100, "concurrency": 5, "failures": 0, "p95_ms": round(p95, 2)}


def remove_probe_user(user_id: int, email: str):
    code = """
import json, sys
from sqlalchemy import delete, select
from app.database import SessionLocal
from app.models import PurchaseRequest, RefreshSession, User
data = json.load(sys.stdin)
if not data["email"].startswith("staging-probe-") or not data["email"].endswith("@example.com"):
    raise SystemExit("Refusing to remove a non-probe identity")
with SessionLocal() as db:
    user = db.get(User, data["user_id"])
    if not user or user.email != data["email"] or user.role != "employee":
        raise SystemExit("Probe identity changed; refusing cleanup")
    if db.scalar(select(PurchaseRequest.id).where(PurchaseRequest.requested_by == user.id).limit(1)):
        raise SystemExit("Probe owns procurement history; refusing cleanup")
    db.execute(delete(RefreshSession).where(RefreshSession.user_id == user.id))
    db.delete(user)
    db.commit()
"""
    compose(
        "exec",
        "-T",
        "backend",
        "python",
        "-c",
        code,
        payload=json.dumps({"user_id": user_id, "email": email}),
    )


def main():
    compose("up", "-d", "--wait", "--wait-timeout", "90")
    compose(
        "cp",
        "web:/data/caddy/pki/authorities/local/root.crt",
        str(RUNTIME / "staging-ca.crt"),
    )
    context = ssl.create_default_context(cafile=str(RUNTIME / "staging-ca.crt"))
    email = f"staging-probe-{uuid.uuid4().hex}@example.com"
    password = secrets.token_urlsafe(24) + "A1"
    user_id = None
    snapshot = None
    restore_script = f"/tmp/staging-restore-{uuid.uuid4().hex}.py"
    report = {"url": BASE, "verified_at": datetime.now(UTC).isoformat()}
    try:
        with httpx.Client(
            base_url=BASE, verify=context, timeout=10, headers={"Origin": BASE}
        ) as client:
            wait_ready(client)
            root = client.get("/")
            root.raise_for_status()
            require("ProcureAI" in root.text, "Production frontend was not served")
            require(
                "frame-ancestors 'none'"
                in root.headers.get("content-security-policy", ""),
                "Frontend CSP is missing",
            )
            require(
                root.headers.get("x-content-type-options") == "nosniff",
                "Frontend security headers are missing",
            )
            require(
                client.get("/orders/123").text == root.text, "SPA deep links are broken"
            )
            require(
                client.get("/assets/missing-staging-probe.js").status_code == 404,
                "Missing assets must not return HTML",
            )
            for path in ("/docs", "/openapi.json", "/redoc"):
                require(
                    client.get(path).status_code == 404,
                    f"{path} is exposed by the proxy",
                )
            require(
                client.get("/api/v1/users").status_code == 401,
                "User list is not protected",
            )
            health = client.get("/api/v1/health")
            require(
                bool(health.headers.get("x-request-id")),
                "Request correlation is missing",
            )
            registered = client.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Staging acceptance probe",
                    "email": email,
                    "password": password,
                },
            )
            registered.raise_for_status()
            user_id = registered.json()["id"]
            login = client.post(
                "/api/v1/auth/login", json={"email": email, "password": password}
            )
            login.raise_for_status()
            cookie = login.headers["set-cookie"].lower()
            require(
                all(
                    flag in cookie for flag in ("secure", "httponly", "samesite=strict")
                ),
                "Refresh cookie security attributes are missing",
            )
            auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
            require(
                client.get("/api/v1/users", headers=auth).status_code == 403,
                "Employee gained administrator access",
            )
            require(
                client.post(
                    "/api/v1/auth/refresh",
                    headers={
                        "Origin": "https://untrusted.invalid",
                    },
                ).status_code
                == 403,
                "Refresh accepted an untrusted origin",
            )
            client.post("/api/v1/auth/refresh").raise_for_status()
            client.post("/api/v1/auth/logout").raise_for_status()
            require(
                client.post("/api/v1/auth/refresh").status_code == 401,
                "Logout did not revoke the refresh session",
            )
            subprocess.run(
                ["npm", "run", "test:e2e"],
                cwd=ROOT / "frontend",
                check=True,
                env={
                    **os.environ,
                    "STAGING_URL": BASE,
                    "STAGING_PROBE_EMAIL": email,
                    "STAGING_PROBE_PASSWORD": password,
                },
            )
            compose("exec", "-T", "backend", "python", "-m", "alembic", "check")
            snapshot = f"/data/backups/acceptance-{uuid.uuid4().hex}.db"
            compose(
                "exec",
                "-T",
                "backend",
                "python",
                "-m",
                "app.manage",
                "backup",
                "--output",
                snapshot,
            )
            compose(
                "exec",
                "-T",
                "backend",
                "python",
                "-c",
                "import pathlib,sys; path=pathlib.Path(sys.argv[1]); "
                "path.write_text(sys.stdin.read()); path.chmod(0o600)",
                restore_script,
                payload=(ROOT / "deploy/restore_probe.py").read_text(),
            )
            result = compose(
                "exec",
                "-T",
                "backend",
                "python",
                restore_script,
                payload=json.dumps(
                    {
                        "snapshot": snapshot,
                        "email": email,
                        "password": password,
                        "user_id": user_id,
                    }
                ),
            )
            print(result)
            report["load_probe"] = asyncio.run(load_probe(context))
            throttled = False
            for index in range(61):
                response = client.post(
                    "/api/v1/auth/refresh",
                    headers={
                        "X-Forwarded-For": f"192.0.2.{index + 1}",
                    },
                )
                if response.status_code == 429:
                    require(
                        response.headers.get("retry-after") == "60",
                        "Authentication throttle lacks Retry-After",
                    )
                    throttled = True
                    break
                require(
                    response.status_code == 401, "Unexpected refresh probe response"
                )
            require(throttled, "Authentication throttle did not activate")
            compose("restart", "backend")
            wait_ready(client)
            profile = client.get("/api/v1/auth/me", headers=auth)
            profile.raise_for_status()
            require(
                profile.json()["id"] == user_id,
                "Restart lost data or changed signing keys",
            )
            report["checks"] = [
                "verified TLS chain",
                "production frontend and SPA routing",
                "security headers",
                "protected API documentation",
                "JWT/RBAC",
                "secure rotating refresh cookies",
                "origin checks",
                "logout",
                "browser login/deep-link/reload",
                "schema parity",
                "online backup",
                "real API login after restore",
                "authentication throttle",
                "restart persistence",
            ]
    finally:
        compose(
            "exec",
            "-T",
            "backend",
            "python",
            "-c",
            "import pathlib,sys; pathlib.Path(sys.argv[1]).unlink(missing_ok=True)",
            restore_script,
        )
        if user_id is not None:
            remove_probe_user(user_id, email)
        if snapshot is not None:
            compose(
                "exec",
                "-T",
                "backend",
                "python",
                "-c",
                "import pathlib,sys; pathlib.Path(sys.argv[1]).unlink(missing_ok=True)",
                snapshot,
            )
    report["probe_data_removed"] = True
    (RUNTIME / "acceptance.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
