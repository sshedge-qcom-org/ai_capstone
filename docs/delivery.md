# Delivery and verification

| Phase | Commit |
| --- | --- |
| 0 | docs: project architecture and planning |
| 1 | feat: initial project setup |
| 2 | feat: authentication and RBAC |
| 3 | feat: procurement dashboard and analytics |
| 4 | feat: purchase request workflow |
| 5 | feat: supplier directory management |
| 6 | feat: AI supplier recommendation engine |
| 7 | feat: order management workflow |
| 8 | feat: threaded discussion system |
| 9 | feat: procurement reporting and exports |
| 10 | feat: production-ready release |

At every application checkpoint: migrate, start application, exercise relevant
HTTP behavior, compile Python, build and lint the frontend, run focused tests,
update README, inspect changed files and commit. Final gate runs all tests plus
browser journey verification. Phase 0 has no executable project: review document
coverage and whitespace instead. Release tag v1.0.0 is created only after the
complete verification gate passes.

Dashboard aggregates are introduced before CRUD phases. Phase 3 therefore creates
the shared request/supplier/order persistence schema and seed records; later phases
add their service/API/UI behavior without disposable fake data or duplicate tables.

## Deployment acceptance boundaries

The implementation must supply secure defaults and working workflows, but a
production rollout still needs organization-specific TLS/proxy configuration,
SMTP/account recovery policy, backups, monitoring and capacity testing. Demo seed
accounts are intentionally local-only. There is no supplier quote/payment
integration or external AI service in scope. No external API key is required.

Next after planning: scaffold both applications, install declared dependencies,
verify migration and health checks, build and test before committing Phase 1.
