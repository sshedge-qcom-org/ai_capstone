import os
import sqlite3
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from app.models import User
from app.rate_limit import LoginLimiter
from app.security import issue_token


def test_token_type_expiry_validation_redaction_and_password_spaces(client, headers):
    headers("employee")
    refresh = client.cookies.get("procureai_refresh")
    assert (
        client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {refresh}",
            },
        ).status_code
        == 401
    )
    expired = issue_token(3, "access", timedelta(seconds=-1))
    assert (
        client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {expired}",
            },
        ).status_code
        == 401
    )
    invalid = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Invalid",
            "email": "invalid@company.com",
            "password": "short",
        },
    )
    assert invalid.status_code == 422
    assert all("input" not in error for error in invalid.json()["detail"])
    data = {
        "full_name": "Space Password",
        "email": "space@company.com",
        "password": " TestPassword123 ",
    }
    assert client.post("/api/v1/auth/register", json=data).status_code == 201
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": data["email"],
                "password": data["password"].strip(),
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": data["email"],
                "password": data["password"],
            },
        ).status_code
        == 200
    )


def test_admin_cannot_orphan_team_and_deactivation_revokes_refresh(client, headers, db):
    headers("employee")
    refresh = client.cookies.get("procureai_refresh")
    admin = headers("admin")
    assert (
        client.patch(
            "/api/v1/users/2",
            headers=admin,
            json={
                "role": "employee",
                "is_active": True,
            },
        ).status_code
        == 409
    )
    assert (
        client.patch(
            "/api/v1/users/3",
            headers=admin,
            json={
                "role": "employee",
                "is_active": False,
                "manager_id": 2,
            },
        ).status_code
        == 200
    )
    db.get(User, 3).is_active = True
    db.commit()
    assert (
        client.post(
            "/api/v1/auth/refresh",
            headers={
                "Cookie": f"procureai_refresh={refresh}",
            },
        ).status_code
        == 401
    )


def test_auth_throttling_returns_retry_after(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "auth_rate_limit", 5)
    for _ in range(5):
        assert client.post("/api/v1/auth/refresh").status_code == 401
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    assert response.headers["x-request-id"]


def test_limiter_recovers_after_window(monkeypatch):
    import app.rate_limit as module

    clock = [100.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    limiter = LoginLimiter()
    assert limiter.allow("client", 1)
    assert not limiter.allow("client", 1)
    clock[0] += 61
    assert limiter.allow("client", 1)


def test_online_backup_preserves_data_and_refuses_overwrite(db, tmp_path):
    destination = tmp_path / "verified-backup.db"
    command = [sys.executable, "-m", "app.manage", "backup", "--output", str(destination)]
    environment = {**os.environ, "DATABASE_URL": str(db.get_bind().url)}
    backend = Path(__file__).resolve().parents[1]
    result = subprocess.run(command, cwd=backend, env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(destination) as backup:
        assert backup.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 4
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert destination.stat().st_mode & 0o777 == 0o600
    original_size = destination.stat().st_size
    repeated = subprocess.run(command, cwd=backend, env=environment, capture_output=True, text=True)
    assert repeated.returncode != 0
    assert "already exists" in repeated.stderr
    assert destination.stat().st_size == original_size
