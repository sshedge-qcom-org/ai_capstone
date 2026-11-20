# Postman lifecycle collection

Import `procurement.postman_collection.json` into Postman. Use only a disposable,
explicitly seeded development API. Set the collection's `password` variable
locally to your demo seed password, keep the cookie jar enabled, then run in order.
The base URL defaults to `http://127.0.0.1:8000/api/v1`.

The collection authenticates as all four demo roles, creates and edits a request,
discusses, approves, recommends, orders, fulfils and exports reports. It also
exercises admin CRUD on temporary categories/suppliers and links the demo vendor
to the selected supplier. Tokens/IDs are captured into local collection variables.
Every request has success assertions. It deliberately creates a real delivered
order; do not run it in production or export populated credentials/tokens.

Regenerate after API workflow changes with
`.venv/bin/python scripts/generate_postman.py`.
The generated collection contains no stored passwords or tokens.

For isolated automated execution, run
`.venv/bin/python scripts/e2e.py --postman`. This starts disposable servers and
runs Chromium plus the actual collection using pinned Newman via `npm exec`.
The optional Newman CLI is downloaded to the npm cache; no production dependency
or credential file is added to the repository.
