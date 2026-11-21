from app.models import User


def test_registration_cannot_escalate_and_normalizes_email(client):
    data = {"full_name": "New Employee", "email": "New@company.com", "password": "TestingOnly123"}
    assert client.post("/api/v1/auth/register", json={**data, "role": "admin"}).status_code == 422
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": "http://127.0.0.1:5173"},
        json=data,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "employee"
    assert "password_hash" not in response.json()
    assert client.post("/api/v1/auth/register", json=data).status_code == 409


def test_login_refresh_rotation_logout(client, headers):
    employee = headers("employee")
    original = client.cookies.get("procureai_refresh")
    assert client.get("/api/v1/auth/me", headers=employee).status_code == 200
    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert client.cookies.get("procureai_refresh") != original
    assert (
        client.post(
            "/api/v1/auth/refresh", headers={"Cookie": f"procureai_refresh={original}"}
        ).status_code
        == 401
    )
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_roles_and_inactive_accounts(client, headers, db):
    assert client.get("/api/v1/users").status_code == 401
    assert client.get("/api/v1/users", headers=headers("employee")).status_code == 403
    assert client.get("/api/v1/users", headers=headers("admin")).status_code == 200
    employee = headers("employee")
    db.get(User, 3).is_active = False
    db.commit()
    assert client.get("/api/v1/auth/me", headers=employee).status_code == 401


def test_cookie_origin_and_invalid_password(client):
    allowed_origin = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={"email": "employee@company.com", "password": "incorrect"},
    )
    assert allowed_origin.status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "employee@company.com",
                "password": "incorrect",
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", headers={"Origin": "https://untrusted.invalid"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Bad",
                "email": "bad@company.com",
                "password": "A1" + "é" * 36,
            },
        ).status_code
        == 422
    )
