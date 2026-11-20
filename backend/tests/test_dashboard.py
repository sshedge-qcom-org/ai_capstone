from decimal import Decimal

from app.models import Order, User
from app.services.seed_data import seed_procurement


def test_dashboard_scopes_and_delivered_spend(client, headers, db):
    seed_procurement(db, db.get(User, 3), db.get(User, 2))
    db.commit()
    result = client.get("/api/v1/dashboard", headers=headers("admin"))
    assert result.status_code == 200
    data = result.json()
    assert data["total_requests"] == 30
    assert data["total_suppliers"] == 30
    assert data["approved_orders"] == 20
    expected = sum(order.amount for order in db.query(Order).filter_by(status="delivered"))
    assert Decimal(str(data["procurement_spend"])) == expected
    assert sum(Decimal(str(row["amount"])) for row in data["monthly_spending"]) == expected
    assert (
        client.get("/api/v1/dashboard", headers=headers("manager")).json()["total_requests"] == 30
    )
    vendor = client.get("/api/v1/dashboard", headers=headers("vendor")).json()
    assert vendor["total_requests"] == 0
    assert vendor["approved_orders"] < 20
    db.get(User, 3).manager_id = None
    db.commit()
    assert client.get("/api/v1/dashboard", headers=headers("manager")).json()["total_requests"] == 0


def test_empty_dashboard(client, headers):
    data = client.get("/api/v1/dashboard", headers=headers("employee")).json()
    assert Decimal(data["procurement_spend"]) == 0
    assert data["monthly_spending"] == []
