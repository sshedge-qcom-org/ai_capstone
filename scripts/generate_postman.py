"""Generate a runnable local-demo Postman lifecycle collection without credentials."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
items = []


def add(name, method, path, body=None, after=()):
    request = {
        "method": method,
        "url": "{{base_url}}" + path,
        "header": [{"key": "Content-Type", "value": "application/json"}],
    }
    if body is not None:
        request["body"] = {"mode": "raw", "raw": json.dumps(body, indent=2)}
    if path in (
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
        "/auth/logout",
        "/health",
    ):
        request["auth"] = {"type": "noauth"}
    tests = [
        'pm.test("Request succeeds", () => pm.expect(pm.response.code).to.be.within(200, 299));'
    ]
    if path in ("/auth/login", "/auth/refresh"):
        tests.append(
            'pm.collectionVariables.set("access_token", pm.response.json().access_token);'
        )
    items.append(
        {
            "name": name,
            "request": request,
            "event": [
                {
                    "listen": "test",
                    "script": {"type": "text/javascript", "exec": [*tests, *after]},
                }
            ],
        }
    )


def login(role):
    add(
        f"Sign in as {role}",
        "POST",
        "/auth/login",
        {"email": f"{role}@company.com", "password": "{{password}}"},
    )


add("Health", "GET", "/health")
add(
    "Register employee",
    "POST",
    "/auth/register",
    {
        "full_name": "Postman Employee",
        "email": "postman-{{$timestamp}}@example.com",
        "password": "{{password}}",
    },
)
login("employee")
add("Current user", "GET", "/auth/me")
add("Rotate refresh cookie", "POST", "/auth/refresh")
add("List categories", "GET", "/categories")
request_body = {
    "title": "Postman verified laptop",
    "description": "Equipment for the engineering onboarding cohort",
    "category": "IT Equipment",
    "quantity": 2,
    "estimated_budget": "2400.50",
    "target_delivery_date": "{{target_delivery_date}}",
}
add(
    "Create request",
    "POST",
    "/requests",
    request_body,
    ['pm.collectionVariables.set("request_id", pm.response.json().id);'],
)
add("List requests", "GET", "/requests?limit=20")
add("Request details", "GET", "/requests/{{request_id}}")
add("Edit pending request", "PATCH", "/requests/{{request_id}}", request_body)
add(
    "Add discussion",
    "POST",
    "/requests/{{request_id}}/comments",
    {"content": "Please include warranty."},
    ['pm.collectionVariables.set("comment_id", pm.response.json().id);'],
)
add(
    "Reply to discussion",
    "POST",
    "/requests/{{request_id}}/comments",
    {
        "content": "Specification attached in the request.",
        "parent_comment_id": "{{comment_id}}",
    },
)
add(
    "Edit discussion",
    "PATCH",
    "/comments/{{comment_id}}",
    {"content": "Please include standard warranty."},
)
add("List discussion roots", "GET", "/requests/{{request_id}}/comments")
add("List replies", "GET", "/requests/{{request_id}}/comments?parent_id={{comment_id}}")
login("manager")
add(
    "Approve team request",
    "POST",
    "/requests/{{request_id}}/decision",
    {"decision": "approved", "reason": "Within departmental budget."},
)
add(
    "Top three recommendations",
    "GET",
    "/requests/{{request_id}}/recommendations",
    after=[
        'pm.test("Three suppliers", () => pm.expect(pm.response.json()).to.have.lengthOf(3));',
        'pm.collectionVariables.set("recommended_supplier_id", pm.response.json()[0].supplier.id);',
    ],
)
add(
    "Create purchase order",
    "POST",
    "/orders",
    {"request_id": "{{request_id}}", "supplier_id": "{{recommended_supplier_id}}"},
    ['pm.collectionVariables.set("order_id", pm.response.json().id);'],
)
add("List orders", "GET", "/orders")
add("Order details", "GET", "/orders/{{order_id}}")
add("Dashboard", "GET", "/dashboard")
add("Procurement reports", "GET", "/reports")
for report in (
    "spending_by_category",
    "supplier_performance",
    "monthly_trends",
    "approval_turnaround",
):
    add(f"Export {report}", "GET", f"/reports/export?report={report}")
login("admin")
add(
    "List users",
    "GET",
    "/users?limit=100",
    after=[
        'pm.collectionVariables.set("vendor_id", pm.response.json().find(u => u.email === "vendor@company.com").id);',
    ],
)
add(
    "Assign vendor to selected supplier",
    "PATCH",
    "/users/{{vendor_id}}",
    {
        "role": "vendor",
        "is_active": True,
        "supplier_id": "{{recommended_supplier_id}}",
    },
)
add("Create category", "POST", "/categories", {"name": "{{demo_category}}"})
add("Delete unused category", "DELETE", "/categories/{{demo_category}}")
add("Search suppliers", "GET", "/suppliers?search=Northstar&limit=20")
add("Supplier details", "GET", "/suppliers/{{recommended_supplier_id}}")
supplier_body = {
    "company_name": "Postman Verification Supplier",
    "category": "IT Equipment",
    "rating": "4.5",
    "average_price_score": "80",
    "average_delivery_days": 7,
    "reliability_score": "95",
    "contact_person": "Verification Team",
    "email": "verification@example.com",
}
add(
    "Create temporary supplier",
    "POST",
    "/suppliers",
    supplier_body,
    ['pm.collectionVariables.set("temporary_supplier_id", pm.response.json().id);'],
)
add("Update supplier", "PATCH", "/suppliers/{{temporary_supplier_id}}", supplier_body)
add("Delete unused supplier", "DELETE", "/suppliers/{{temporary_supplier_id}}")
login("vendor")
add("Assigned vendor orders", "GET", "/orders")
for status in ("processing", "shipped", "delivered"):
    add(
        f"Mark order {status}",
        "PATCH",
        "/orders/{{order_id}}/status",
        {"status": status},
    )
login("employee")
add("Delete own comment (preserve replies)", "DELETE", "/comments/{{comment_id}}")
add("Sign out", "POST", "/auth/logout")
collection = {
    "info": {
        "name": "AI Procurement Platform - local lifecycle",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        "description": "Run in order against explicitly seeded development data. Set password locally. "
        "Creates a real delivered order and updates the demo vendor assignment. "
        "Do not run against production.",
    },
    "auth": {
        "type": "bearer",
        "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
    },
    "variable": [
        {"key": "base_url", "value": "http://127.0.0.1:8000/api/v1"},
        {"key": "password", "value": ""},
        {"key": "access_token", "value": ""},
    ],
    "event": [
        {
            "listen": "prerequest",
            "script": {
                "type": "text/javascript",
                "exec": [
                    'pm.collectionVariables.set("target_delivery_date", new Date(Date.now() + 14 * 86400000).toISOString().slice(0,10));',
                    'if (!pm.collectionVariables.get("demo_category")) pm.collectionVariables.set("demo_category", "Postman " + Date.now());',
                ],
            },
        }
    ],
    "item": items,
}
directory = root / "postman"
directory.mkdir(exist_ok=True)
(directory / "procurement.postman_collection.json").write_text(
    json.dumps(collection, indent=2) + "\n"
)
print(f"Generated {len(items)} requests.")
