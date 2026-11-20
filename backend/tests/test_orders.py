from decimal import Decimal

from app.models import PurchaseRequest, Supplier, User
from app.services.seed_data import seed_procurement


def test_order_lifecycle_scope_and_analytics(client, headers, db):
    seed_procurement(db, db.get(User, 3), db.get(User, 2))
    db.commit()
    request = db.query(PurchaseRequest).filter_by(status="approved").first()
    supplier = db.query(Supplier).filter_by(category=request.category).first()
    db.get(User, 4).supplier_id = supplier.id
    db.commit()
    manager, vendor = headers("manager"), headers("vendor")
    before = client.get("/api/v1/dashboard", headers=manager).json()["procurement_spend"]
    response = client.post(
        "/api/v1/orders",
        headers=manager,
        json={
            "request_id": request.id,
            "supplier_id": supplier.id,
        },
    )
    assert response.status_code == 201
    order = response.json()
    assert Decimal(order["amount"]) == request.estimated_budget
    assert (
        client.post(
            "/api/v1/orders",
            headers=manager,
            json={
                "request_id": request.id,
                "supplier_id": supplier.id,
            },
        ).status_code
        == 400
    )
    path = f"/api/v1/orders/{order['id']}"
    assert (
        client.patch(f"{path}/status", headers=manager, json={"status": "processing"}).status_code
        == 403
    )
    assert (
        client.patch(f"{path}/status", headers=vendor, json={"status": "delivered"}).status_code
        == 400
    )
    for status in ("processing", "shipped", "delivered"):
        assert (
            client.patch(f"{path}/status", headers=vendor, json={"status": status}).status_code
            == 200
        )
    detail = client.get(path, headers=vendor).json()
    assert detail["delivery_date"]
    assert len(detail["history"]) == 4
    assert client.get("/api/v1/dashboard", headers=manager).json()["procurement_spend"] == float(
        Decimal(str(before)) + request.estimated_budget
    )
    db.get(User, 4).supplier_id = None
    db.commit()
    assert client.get(path, headers=vendor).status_code == 404


def test_order_requires_approval_and_matching_category(client, headers, db):
    seed_procurement(db, db.get(User, 3), db.get(User, 2))
    db.commit()
    manager = headers("manager")
    pending = db.query(PurchaseRequest).filter_by(status="pending").first()
    approved = db.query(PurchaseRequest).filter_by(status="approved").first()
    wrong = db.query(Supplier).filter(Supplier.category != approved.category).first()
    assert (
        client.post(
            "/api/v1/orders",
            headers=manager,
            json={
                "request_id": pending.id,
                "supplier_id": wrong.id,
            },
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/orders",
            headers=manager,
            json={
                "request_id": approved.id,
                "supplier_id": wrong.id,
            },
        ).status_code
        == 422
    )
