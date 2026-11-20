from decimal import Decimal

from app.models import PurchaseRequest, Supplier, User
from app.services.recommendations import score_supplier
from app.services.seed_data import seed_procurement


def test_weighted_score_and_monotonicity():
    supplier = Supplier(
        id=1,
        company_name="Test",
        category="IT",
        rating=Decimal("5"),
        average_price_score=Decimal("100"),
        average_delivery_days=7,
        reliability_score=Decimal("100"),
        contact_person="Test",
        email="test@example.com",
    )
    result = score_supplier(supplier)
    assert result["score"] == Decimal("90.00")
    assert result["contributions"] == {
        "price": Decimal("40"),
        "rating": Decimal("25"),
        "delivery": Decimal("10"),
        "reliability": Decimal("15"),
    }
    supplier.average_delivery_days = 14
    assert score_supplier(supplier)["score"] < result["score"]
    supplier.average_price_score = Decimal(0)
    assert score_supplier(supplier)["score"] < Decimal(50)


def test_top_three_category_scope_and_approval_gate(client, headers, db):
    seed_procurement(db, db.get(User, 3), db.get(User, 2))
    db.commit()
    request = db.query(PurchaseRequest).filter_by(status="approved").first()
    path = f"/api/v1/requests/{request.id}/recommendations"
    manager = headers("manager")
    response = client.get(path, headers=manager)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(row["supplier"]["category"] == request.category for row in data)
    assert [Decimal(row["score"]) for row in data] == sorted(
        [Decimal(row["score"]) for row in data], reverse=True
    )
    assert client.get(path, headers=headers("employee")).status_code == 403
    request.status = "pending"
    db.commit()
    assert client.get(path, headers=manager).status_code == 400


def test_ties_are_stable_and_empty_categories_return_empty(client, headers, db):
    seed_procurement(db, db.get(User, 3), db.get(User, 2))
    db.commit()
    request = db.query(PurchaseRequest).filter_by(status="approved").first()
    suppliers = db.query(Supplier).filter_by(category=request.category).all()
    for supplier in suppliers:
        supplier.rating = Decimal(4)
        supplier.average_price_score = Decimal(80)
        supplier.average_delivery_days = 7
        supplier.reliability_score = Decimal(90)
    db.commit()
    path = f"/api/v1/requests/{request.id}/recommendations"
    result = client.get(path, headers=headers("manager")).json()
    assert [row["supplier"]["id"] for row in result] == sorted(s.id for s in suppliers)[:3]
    from app.models import Category

    db.add(Category(name="No suppliers"))
    db.flush()
    request.category = "No suppliers"
    db.commit()
    assert client.get(path, headers=headers("manager")).json() == []
