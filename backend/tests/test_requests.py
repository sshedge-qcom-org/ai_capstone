from datetime import date, timedelta

import pytest

from app.models import Category, User


@pytest.fixture
def payload(db):
    db.add(Category(name="IT Equipment"))
    db.commit()
    return {
        "title": "Engineering laptop",
        "description": "Required for new engineering hire",
        "category": "IT Equipment",
        "quantity": 2,
        "estimated_budget": "2500.50",
        "target_delivery_date": (date.today() + timedelta(days=14)).isoformat(),
    }


def test_revision_approval_and_immutable_approved_request(client, headers, payload):
    employee = headers("employee")
    response = client.post("/api/v1/requests", headers=employee, json=payload)
    assert response.status_code == 201
    path = f"/api/v1/requests/{response.json()['id']}"
    manager = headers("manager")
    assert (
        client.post(f"{path}/decision", headers=manager, json={"decision": "revision"}).status_code
        == 422
    )
    assert (
        client.post(
            f"{path}/decision",
            headers=manager,
            json={
                "decision": "revision",
                "reason": "Please reduce quantity",
            },
        ).json()["status"]
        == "revision"
    )
    assert (
        client.patch(path, headers=employee, json={**payload, "quantity": 1}).json()["status"]
        == "pending"
    )
    assert (
        client.post(f"{path}/decision", headers=manager, json={"decision": "approved"}).json()[
            "status"
        ]
        == "approved"
    )
    assert client.patch(path, headers=employee, json=payload).status_code == 400
    assert (
        client.post(
            f"{path}/decision",
            headers=manager,
            json={"decision": "rejected", "reason": "Duplicate"},
        ).status_code
        == 400
    )
    assert len(client.get(path, headers=employee).json()["history"]) == 2


def test_scope_and_validation(client, headers, payload, db):
    employee = headers("employee")
    assert (
        client.post(
            "/api/v1/requests", headers=employee, json={**payload, "estimated_budget": "-1"}
        ).status_code
        == 422
    )
    result = client.post("/api/v1/requests", headers=employee, json=payload).json()
    path = f"/api/v1/requests/{result['id']}"
    assert (
        client.post(f"{path}/decision", headers=employee, json={"decision": "approved"}).status_code
        == 403
    )
    assert client.get(path, headers=headers("vendor")).status_code == 403
    db.get(User, 3).manager_id = None
    db.commit()
    assert client.get(path, headers=headers("manager")).status_code == 404
    assert client.get(path, headers=headers("admin")).status_code == 200
    assert client.get("/api/v1/requests?limit=101", headers=employee).status_code == 422
