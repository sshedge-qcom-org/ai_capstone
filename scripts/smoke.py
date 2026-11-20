"""Verify the running local API using explicitly seeded development accounts."""

import os

import httpx

base = os.environ.get("API_URL", "http://127.0.0.1:8000/api/v1")
password = os.environ["DEMO_PASSWORD"]
with httpx.Client(base_url=base, timeout=15) as client:
    client.get("/health").raise_for_status()
    for role in ("admin", "manager", "employee", "vendor"):
        response = client.post(
            "/auth/login",
            json={
                "email": f"{role}@company.com",
                "password": password,
            },
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        client.get(
            "/orders", headers={"Authorization": f"Bearer {token}"}
        ).raise_for_status()
        profile = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        profile.raise_for_status()
        assert profile.json()["role"] == role
        dashboard = client.get(
            "/dashboard", headers={"Authorization": f"Bearer {token}"}
        )
        dashboard.raise_for_status()
        assert "monthly_spending" in dashboard.json()
        if role in ("manager", "admin"):
            client.get(
                "/reports", headers={"Authorization": f"Bearer {token}"}
            ).raise_for_status()
            client.get(
                "/reports/export?report=monthly_trends",
                headers={"Authorization": f"Bearer {token}"},
            ).raise_for_status()
            auth = {"Authorization": f"Bearer {token}"}
            approved = client.get("/requests?status=approved&limit=1", headers=auth)
            approved.raise_for_status()
            if approved.json():
                request_id = approved.json()[0]["id"]
                result = client.get(
                    f"/requests/{request_id}/recommendations", headers=auth
                )
                result.raise_for_status()
                assert len(result.json()) <= 3
        if role != "vendor":
            visible = client.get(
                "/requests?limit=1", headers={"Authorization": f"Bearer {token}"}
            )
            visible.raise_for_status()
            if visible.json():
                request_id = visible.json()[0]["id"]
                client.get(
                    f"/requests/{request_id}/comments",
                    headers={"Authorization": f"Bearer {token}"},
                ).raise_for_status()
            client.get(
                "/suppliers", headers={"Authorization": f"Bearer {token}"}
            ).raise_for_status()
            client.get(
                "/requests", headers={"Authorization": f"Bearer {token}"}
            ).raise_for_status()
        client.post("/auth/refresh").raise_for_status()
        client.post("/auth/logout").raise_for_status()
print("Live health and all four authentication journeys passed.")
