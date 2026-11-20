# User guide

## Employee

Register with your company email, then ask an admin to assign your manager.
Open **Purchase requests → New request**. Enter the item, category, quantity,
estimated **total** budget in USD, justification and target delivery date.
Submitting creates a Pending request. Edit while Pending, or revise and resubmit
when a manager sends it back. Approved/rejected/ordered requests are immutable.
The detail screen shows decisions and threaded discussion. Track fulfilment
through **Orders**.

## Manager

Your scope is employees assigned to you by an administrator. Filter the request
queue, inspect justification and discuss details. Approve, reject with a reason,
or send back for revision with a reason. You cannot approve your own requests.

Approved requests show up to three suppliers matching their category. Scores use
40% price value, 25% rating, 20% delivery speed and 15% reliability. Expand score
contributions to inspect the ranking. The score is explainable decision support,
not a supplier quote or a trained model's prediction.

Choose **Select & create order** and confirm the supplier. The order snapshots
the approved estimated budget; only one order can be created per request.
Use **Reports** for team spending, delivery performance, trends and turnaround.

## Vendor

An admin links your account to a supplier. You can see only that supplier's
orders. Open an order and confirm each next step: Processing, Shipped, Delivered.
You cannot skip or reverse steps. Delivery records completion time and updates
financial analytics. Vendors cannot read internal requests or discussions.

## Admin

**Administration** manages account roles, activation, manager IDs, supplier IDs
and categories. Users initially register as employees; convert a registered user
to manager or vendor as needed. Assign a supplier before activating a vendor.
Reassign a manager's employees before demoting or deactivating that manager.
You cannot demote/deactivate yourself.

**Suppliers** supports search, category filtering, details, create, update and
delete. Price value is a 0–100 affordability score: higher is better. Historical
orders prevent supplier deletion/category changes. Categories in use cannot be
deleted. Admins see company-wide analytics and may moderate comment deletion.

## Reports and discussions

Dates are UTC. Procurement spend counts delivered orders only and uses the order's
approved estimated value. Supplier performance date filters refer to order date;
financial trends refer to delivery date. Approval turnaround uses the first final
decision, excluding revision events. CSV files are sanitized for spreadsheets.

Comments support eight nested reply levels. Expand replies to load them; each
level has its own pagination. Authors may edit/delete; deletion leaves a
tombstone so replies remain readable.

## Troubleshooting

- **Empty team queue:** check employee manager assignments.
- **Empty vendor orders:** check the account's supplier assignment.
- **No recommendations:** add suppliers in the request's category.
- **Conflict:** someone changed the record; refresh before retrying.
- **429:** wait one minute before retrying authentication.
- **503:** the database is temporarily unavailable; retry, then contact operations.
- **Session expired:** sign in again. Unsaved forms are not persisted.
