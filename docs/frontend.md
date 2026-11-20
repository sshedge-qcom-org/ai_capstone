# Frontend page map

| Route | Page | Roles |
| --- | --- | --- |
| / | Public landing | All |
| /login | Login | Public |
| /register | Employee registration | Public |
| /dashboard | KPIs, spending, approval chart, role-specific actions | All authenticated |
| /requests | Search/list, status, create action | Employee, manager, admin |
| /requests/new | Validated request form | Employee |
| /requests/:id | Details, decisions, recommendations, threaded discussion | Resource-scoped non-vendor |
| /requests/:id/edit | Edit/resubmit | Employee owner |
| /suppliers | Search/filter and admin CRUD | Employee, manager, admin |
| /suppliers/:id | Supplier details | Employee, manager, admin |
| /orders | Scoped order list | All authenticated |
| /orders/:id | Details and linear fulfilment timeline | Resource-scoped |
| /reports | Charts and CSV exports | Manager, admin |
| /admin | User/role and category management | Admin |
| * | Not found | All |

App shell: responsive navigation, identity/role, sign out, main landmark and skip
link. Every form has labels, field validation, submit progress and explicit error
feedback. Async screens have loading, empty and error states. Status is expressed
as text, not color alone. Charts have text/table equivalents. Mutations refresh
authoritative data. Confirmation is required for destructive operations.

Auth context restores sessions via the refresh endpoint. Axios attaches in-memory
access tokens; a single refresh attempt handles expiry and then redirects to login
on failure. Role guards hide inaccessible routes, but API checks remain definitive.
