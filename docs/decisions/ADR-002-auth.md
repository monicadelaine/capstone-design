# ADR-002: Keep Auth0 for login; move role assignment server-side

**Status:** Accepted
**Date:** 2026-09-22
**Deciders:** Gaurav Shrivastava, Jayden White, Margulan Baizhakyp, Noland Miller

## Context

v1 authenticates through Auth0. Roles (student, sponsor, admin) are not stored in our database; they live in a token claim set by two Auth0 Actions. The role is chosen at signup by a client-supplied hint, which the prior team's own README calls "highly likely vulnerable to role spoofing." Student signups are restricted to `@crimson.ua.edu` inside the Auth0 Action. Separately, the backend never checks roles: every endpoint that requires login accepts any role, and two endpoint groups (semesters, emails) require no login at all.

The dev environment currently reuses the prior team's Auth0 tenant and client ID. We do not control that tenant.

## Options considered

1. **Keep Auth0.** Create our own tenant; keep the login flow the users and the sponsor already know. Tradeoff: an external dependency and a free-tier limit, and the role-assignment Actions must be rewritten.
2. **UA single sign-on (MySSO).** Best experience for students. Tradeoff: requires a request to UA OIT with unknown lead time; the prior team never got it configured. Not achievable for Iteration 1.
3. **Plain Django email/password login.** Simplest, fully under our control. Tradeoff: we own password reset, email verification, and sponsor social login, all of which Auth0 gives us for free.

## Decision

Option 1 for this semester, with three changes:

- Create a tenant the team and sponsor control; retire the prior team's tenant and client ID from all env templates.
- Role is decided server-side. Students are recognized because their email exists in the Student table (imported by the admin from Blackboard). Sponsors are everyone else who signs up. Admin is granted only by an existing admin in our database, not by an Auth0 role. The client-supplied role hint is removed.
- Add a role-based permission class to the API and require authentication on the semester and email endpoints.

Revisit MySSO as a recommendation in the handoff documentation if the sponsor wants it.

## Consequences

- Login UI stays as-is for Iteration 1; the security work is backend-only and testable.
- A `role` field is added to our user data (see [development-guide/data-model.md](../development-guide/data-model.md)).
- The Auth0 Actions from the prior team's Cloud-V2 branch are not reused.
- New backlog items: create Auth0 tenant; permission class; authenticate open endpoints; remove role hint from signup.
