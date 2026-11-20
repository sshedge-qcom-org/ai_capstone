# API contract

Base path `/api/v1`; JSON except CSV. FastAPI `/docs` and `/openapi.json` are
the executable API reference. Dates are ISO 8601. Money serializes as decimal
strings. Collection parameters: `offset=0`, `limit=50` (maximum 100).
Collection responses are arrays; dashboard/report responses are named objects.

Errors use `{"detail": "message"}` or Pydantic's field-error array.
400 invalid transition, 401 unauthenticated, 403 forbidden, 404 invisible/missing
resource, 409 conflict, 422 invalid fields. Unexpected errors return a generic
500 with a request ID, never a stack trace.

| Method | Path | Access / purpose |
| --- | --- | --- |
| GET | /health | Public database readiness |
| POST | /auth/register | Public; name, email, password; employee only |
| POST | /auth/login | Public; email/password; access token + refresh cookie |
| POST | /auth/refresh | Refresh cookie; rotate session |
| POST | /auth/logout | Revoke refresh cookie/session |
| GET | /auth/me | Authenticated user profile |
| GET | /users | Admin; paginated users |
| PATCH | /users/{id} | Admin; role, active, manager and supplier assignment |
| GET | /categories | Non-vendor; configured categories |
| POST | /categories | Admin; unique name |
| DELETE | /categories/{name} | Admin; only if unreferenced |
| GET | /dashboard | Role-scoped KPI, status and monthly trend aggregates |
| GET | /requests | Employee own / manager team / admin all |
| POST | /requests | Employee; create pending request |
| GET | /requests/{id} | Resource-scoped detail, approval history |
| PATCH | /requests/{id} | Owner; pending/revision only |
| POST | /requests/{id}/decision | Team manager/admin; decision and reason |
| GET | /suppliers | Non-vendor; search and category filters |
| GET | /suppliers/{id} | Non-vendor |
| POST | /suppliers | Admin |
| PATCH | /suppliers/{id} | Admin |
| DELETE | /suppliers/{id} | Admin; 409 if referenced |
| GET | /requests/{id}/recommendations | Scoped manager/admin; approved only |
| GET | /orders | Employee own / manager team / admin all / vendor assigned |
| POST | /orders | Manager/admin; request_id + supplier_id |
| GET | /orders/{id} | Scoped detail + status history |
| PATCH | /orders/{id}/status | Assigned vendor/admin; next status |
| GET | /requests/{id}/comments | Same visibility as request |
| POST | /requests/{id}/comments | Scoped non-vendor; content + optional parent |
| PATCH | /comments/{id} | Author only; content |
| DELETE | /comments/{id} | Author/admin; tombstone |
| GET | /reports | Manager team / admin all; spend/category, supplier performance, monthly trends, turnaround |
| GET | /reports/export?report=... | Same scope; CSV, spreadsheet-injection safe |

Dashboard spend and financial reports count delivered orders only, by delivery
month. Approved orders counts all orders. Supplier performance distinguishes
open from delivered orders. Approval turnaround uses the first final decision
(approval/rejection), excluding revision events. Empty aggregates return zeros
and empty arrays, not invented chart data.
