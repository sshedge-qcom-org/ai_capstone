import csv
import io
from decimal import Decimal

from app.models import Supplier, User
from app.services.reports import safe_cell
from app.services.seed_data import seed_history, seed_procurement


def test_reports_reconcile_scope_and_export(client, headers, db):
    manager = db.get(User, 2)
    seed_procurement(db, db.get(User, 3), manager)
    seed_history(db, manager)
    db.commit()
    admin = headers("admin")
    response = client.get("/api/v1/reports", headers=admin)
    assert response.status_code == 200
    data = response.json()
    spend = Decimal(str(client.get("/api/v1/dashboard", headers=admin).json()["procurement_spend"]))
    assert sum(Decimal(str(row["amount"])) for row in data["spending_by_category"]) == spend
    assert sum(Decimal(str(row["amount"])) for row in data["monthly_trends"]) == spend
    assert all(24 <= row["average_hours"] <= 48 for row in data["approval_turnaround"])
    supplier = db.get(Supplier, 1)
    supplier.company_name = '=HYPERLINK("malicious")'
    db.commit()
    exported = client.get("/api/v1/reports/export?report=supplier_performance", headers=admin)
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]
    rows = list(csv.DictReader(io.StringIO(exported.text.lstrip("\ufeff"))))
    assert any(row["supplier"].startswith("'=") for row in rows)
    db.get(User, 3).manager_id = None
    db.commit()
    assert client.get("/api/v1/reports", headers=headers("manager")).json()["monthly_trends"] == []
    assert client.get("/api/v1/reports", headers=headers("employee")).status_code == 403
    assert client.get("/api/v1/reports/export?report=unknown", headers=admin).status_code == 422
    assert (
        client.get("/api/v1/reports?since=2026-03-01&until=2026-01-01", headers=admin).status_code
        == 422
    )


def test_safe_csv_cells():
    for cell in ("=1+1", " +SUM(A1)", "@formula", "\t=1", "-cmd"):
        assert safe_cell(cell).startswith("'")
    assert safe_cell(Decimal("-1.25")) == Decimal("-1.25")
    assert safe_cell("Ordinary supplier") == "Ordinary supplier"
