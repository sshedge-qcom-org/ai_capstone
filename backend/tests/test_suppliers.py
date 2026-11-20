from app.models import User
from app.services.seed_data import seed_procurement


def test_directory_filter_crud_and_references(client, headers, db):
    seed_procurement(db, db.get(User, 3), db.get(User, 2))
    db.commit()
    employee, admin = headers("employee"), headers("admin")
    data = client.get("/api/v1/suppliers?category=IT%20Equipment", headers=employee).json()
    assert len(data) == 6
    assert client.get("/api/v1/suppliers?search=Northstar", headers=employee).json()
    assert client.get("/api/v1/suppliers", headers=headers("vendor")).status_code == 403
    payload = {key: value for key, value in data[0].items() if key != "id"}
    assert client.post("/api/v1/suppliers", headers=employee, json=payload).status_code == 403
    created = client.post("/api/v1/suppliers", headers=admin, json=payload)
    assert created.status_code == 201
    path = f"/api/v1/suppliers/{created.json()['id']}"
    assert client.patch(path, headers=admin, json={**payload, "rating": 6}).status_code == 422
    assert client.patch(path, headers=admin, json={**payload, "rating": "4.90"}).status_code == 200
    assert client.delete(path, headers=admin).status_code == 204
    assert client.delete("/api/v1/suppliers/1", headers=admin).status_code == 409
    assert client.delete("/api/v1/categories/IT%20Equipment", headers=admin).status_code == 409
    assert (
        client.post("/api/v1/categories", headers=admin, json={"name": "Travel"}).status_code == 201
    )
    assert (
        client.post("/api/v1/categories", headers=admin, json={"name": "Travel"}).status_code == 409
    )
    assert client.delete("/api/v1/categories/Travel", headers=admin).status_code == 204
