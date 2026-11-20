from app.models import PurchaseRequest, User
from app.services.seed_data import seed_procurement


def test_threads_edit_permissions_and_tombstones(client, headers, db):
    seed_procurement(db, db.get(User, 3), db.get(User, 2))
    db.commit()
    requests = db.query(PurchaseRequest).limit(2).all()
    path = f"/api/v1/requests/{requests[0].id}/comments"
    employee, manager = headers("employee"), headers("manager")
    root = client.post(
        path, headers=employee, json={"content": "Please review this specification."}
    )
    assert root.status_code == 201
    root_id = root.json()["id"]
    reply = client.post(
        path, headers=manager, json={"content": "Looks good.", "parent_comment_id": root_id}
    )
    assert reply.status_code == 201
    assert (
        client.post(
            f"/api/v1/requests/{requests[1].id}/comments",
            headers=employee,
            json={
                "content": "Wrong thread",
                "parent_comment_id": root_id,
            },
        ).status_code
        == 422
    )
    assert len(client.get(path, headers=employee).json()) == 1
    assert len(client.get(f"{path}?parent_id={root_id}", headers=employee).json()) == 1
    assert (
        client.patch(
            f"/api/v1/comments/{root_id}", headers=manager, json={"content": "Unauthorized edit"}
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/v1/comments/{root_id}",
            headers=employee,
            json={"content": "Revised specification"},
        ).status_code
        == 200
    )
    assert client.delete(f"/api/v1/comments/{root_id}", headers=employee).status_code == 204
    result = client.get(path, headers=manager).json()[0]
    assert result["content"] == "[deleted]" and result["reply_count"] == 1
    assert (
        client.patch(
            f"/api/v1/comments/{root_id}", headers=employee, json={"content": "Resurrect"}
        ).status_code
        == 400
    )
    db.get(User, 3).manager_id = None
    db.commit()
    assert client.get(path, headers=manager).status_code == 404


def test_reply_depth_limit_and_empty_content(client, headers, db):
    seed_procurement(db, db.get(User, 3), db.get(User, 2))
    db.commit()
    path = f"/api/v1/requests/{db.query(PurchaseRequest).first().id}/comments"
    employee = headers("employee")
    assert client.post(path, headers=employee, json={"content": "  "}).status_code == 422
    parent = None
    for _ in range(9):
        result = client.post(
            path, headers=employee, json={"content": "Nested reply", "parent_comment_id": parent}
        )
        assert result.status_code == 201
        parent = result.json()["id"]
    assert (
        client.post(
            path,
            headers=employee,
            json={
                "content": "Too deep",
                "parent_comment_id": parent,
            },
        ).status_code
        == 422
    )
