# Architecture Decision Records

**Audience:** developers and future maintainers.

One file per decision a future developer needs in order to understand the system. Small, change-local decisions belong in the pull request that made them, not here.

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](ADR-001-stack.md) | Build on the v1 codebase (Vue 3 + Django REST + PostgreSQL) rather than rebuild | Accepted |
| [ADR-002](ADR-002-auth.md) | Keep Auth0 for login; move role assignment server-side | Accepted; see its "As built" section |
| [ADR-003](ADR-003-hosting.md) | Host on one Google Cloud VM with Docker Compose | Accepted |
| [ADR-004](ADR-004-assignment-solver.md) | Assign teams with a constraint solver, and do not store proposals | Accepted |
| [ADR-005](ADR-005-file-storage.md) | Store uploads in Google Cloud Storage and serve them through Django | Accepted |
| [ADR-006](ADR-006-instructor-tools-in-django-admin.md) | Build the instructor's tools in Django admin | Accepted |

ADR-003 to ADR-006 were written on 2026-11-21 to record decisions made during Iterations 2 and 3; each names the pull requests it was recorded from. Options that were investigated and not chosen are also summarised in [Recommendations](../recommendations/README.md#6-considered-and-decided-against).

Template: [ADR-template.md](ADR-template.md)
