# Architecture Decision Records

**Audience:** developers and future maintainers.

One file per decision a future developer needs in order to understand the system. Small, change-local decisions belong in the pull request that made them, not here.

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](ADR-001-stack.md) | Build on the v1 codebase (Vue 3 + Django REST + PostgreSQL) rather than rebuild | Accepted |
| [ADR-002](ADR-002-auth.md) | Keep Auth0 for login; move role assignment server-side | Accepted |

Template: [ADR-template.md](ADR-template.md)
