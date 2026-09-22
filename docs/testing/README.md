# Testing Plan

**Audience:** developers.

**Status:** placeholder. Filled in as the corresponding work is delivered.

Test plan and how to run the suites. Today: `docker compose -f docker-compose.dev.yml exec backend pytest -q` for the backend (188 tests), `npm run test` in `frontend/` for the frontend. CI runs the backend suite on every push and pull request.
