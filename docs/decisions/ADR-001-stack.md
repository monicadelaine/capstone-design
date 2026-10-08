# ADR-001: Build on the v1 codebase rather than rebuild

**Status:** Accepted
**Date:** 2026-09-22
**Deciders:** Gaurav Shrivastava, Jayden White, Margulan Baizhakyp, Noland Miller

## Context

The sponsor handed us the Spring 2026 team's working application: Vue 3 + Vite frontend, Django REST Framework backend, PostgreSQL, Auth0 login, MinIO/S3 storage, Docker Compose. It runs, has 188 passing backend tests, and implements the core semester workflow (sponsor submission, student ranking, manual assignment, sponsor emails). Its gaps are documented in [docs/investigations/v1-reference.md](../investigations/v1-reference.md).

The course requires a live demo of integrated working software at each iteration, the first on 9/24, and a full handoff at semester end. Four developers, roughly ten working weeks.

## Options considered

1. **Build on v1.** Keep the stack and the code. Fix the security gaps, delete dead code, pin dependencies, add the features the sponsor needs. Tradeoff: we inherit some design choices we would not make ourselves, and the codebase has rough edges (unpinned dependencies, dead components, hardcoded values).
2. **Rebuild on the same stack.** Same technologies, fresh code, using v1 only as a reference. Tradeoff: the first two iterations reproduce what already exists before any new value ships.
3. **Rebuild on a different stack** (for example Next.js with a hosted database). Tradeoff: more learning value for the team, but the highest schedule risk, and the team's shared experience is stronger in Python.

## Decision

Option 1. The parts that matter to the sponsor and are missing from v1 (a proposed-assignment feature, student notifications, an admin dashboard, sponsor visibility) are new work under every option. Rebuilding does not make them cheaper; it delays them. The worst v1 problems are small fixes: a permission class for role checks, a server-side deadline check, database constraints, authentication on two open endpoints.

## Consequences

- Iteration 1 can demo real software: the dev environment (PR #27, #28) and CI already run against this code.
- We owe a cleanup pass early: remove the six unrouted Vue components and unrouted email views, pin `backend/requirements.txt`, replace hardcoded year and CORS origins. Tracked in the backlog.
- Deployment is ours to build. The prior team's cloud configuration lived on an unmerged branch under their personal accounts and is no longer running.
- The preliminary presentation described a ground-up build. This ADR supersedes that framing; the Iteration 1 presentation states the decision and this reasoning.
