# Testing

**Audience:** developers.

Two automated suites exist, and both run inside the dev containers. Counts are as of 2026-09-24 and will grow.

| Suite | Runner | Where the tests live | Tests |
|---|---|---|---|
| Backend | `pytest` with `pytest-django` | `backend/<app>/tests/` | 203 |
| Frontend | `vitest` with `@vue/test-utils` and `jsdom` | `frontend/src/**/*.test.js` | 36 |

## Run everything with one command

The dev stack must be running first: `docker compose -f docker-compose.dev.yml up -d`.

| Shell | Both suites | One suite |
|---|---|---|
| macOS, Linux, Git Bash | `scripts/test.sh` | `scripts/test.sh backend` or `scripts/test.sh frontend` |
| Windows PowerShell | `.\scripts\test.ps1` | `.\scripts\test.ps1 backend` or `.\scripts\test.ps1 frontend` |

Both suites always run, even if the first one fails, and the exit code is non-zero if either fails. This is the command to run before pushing a branch.

## Run a suite directly

Backend, from the repository root:

```
docker compose -f docker-compose.dev.yml exec backend pytest -q                      # everything
docker compose -f docker-compose.dev.yml exec backend pytest project/tests -q        # one app
docker compose -f docker-compose.dev.yml exec backend pytest project/tests/test_views.py -k limit -q   # one file, tests matching a word
docker compose -f docker-compose.dev.yml exec backend pytest --cov                   # with coverage
```

Frontend, from the repository root:

```
docker compose -f docker-compose.dev.yml exec frontend npm run test                                   # everything, once
docker compose -f docker-compose.dev.yml exec frontend npx vitest run src/components/Sidebar.test.js  # one file
docker compose -f docker-compose.dev.yml exec frontend npm run test:watch                             # re-run on change (needs a terminal)
docker compose -f docker-compose.dev.yml exec frontend npm run test:coverage                          # with coverage
```

## What is covered

**Backend**, by Django app:

- `project`: model validation and constraints for Project, Semester, Preference, Assignment, Feedback, and Attachment; serializers, including the sponsor ownership and `projects_allowed` rules; API views for projects (CRUD, filters, and who may write by role), preferences, assignments, and feedback; admin actions for project status, semester membership, and assigning students to projects.
- `user`: Sponsor and Student models and validators (phone, CWID); serializers; the sponsor and student endpoints and the profile endpoint; sponsor admin email actions.
- `emails`: email serializers; the send endpoints; the email client, template rendering, and EML export helpers; the custom admin views.

**Frontend**:

- `services/api.test.js`: bearer token handling, endpoint URLs, student data normalization.
- `stores/`: `projectsStore` and `studentStore` fetch flows, fallbacks, getters, and reset.
- `components/`: ConfirmationModal, EmailForm, ProjectPresentation, Sidebar, SponsorOutreach, and SponsorProjectForm (profile line, project-limit lockout, submit payload and in-flight lock, inline server errors).

The backend README has a fuller per-file breakdown under "Unit Tests (Pytest)".

## Where tests run automatically

`.github/workflows/test.yml` runs both suites as separate jobs, `backend` and `frontend`, on every push and pull request. The backend job installs from `backend/requirements.txt` on Python 3.12; the frontend job runs `npm ci` and `npm run test` on Node 24 to match the Dockerfile. A pull request should not be merged with a red check.

## Conventions

- **Backend:** put tests in the app that owns the behavior, under `<app>/tests/`, split by layer (`test_models.py`, `test_serializers.py`, `test_views.py`, `test_admin.py`). API tests authenticate with `make_client(email, roles)` in `project/tests/test_views.py`, which forces an Auth0-style user carrying roles; use the `sponsor_client`, `student_client`, or admin `api_client` fixtures to cover permission paths. Mock email and SMTP with `monkeypatch` so tests never touch the network.
- **Frontend:** name files `*.test.js` next to the code they test. Mock `vue-router`, `@auth0/auth0-vue`, and `../services/api` with `vi.hoisted` plus `vi.mock`, as `Sidebar.test.js` does. A component that uses FormKit needs the FormKit plugin installed on mount and a short real-timer wait before submitting, because FormKit validates on a debounce; see `SponsorProjectForm.test.js`.
- **New behavior needs a test** at each layer where logic lives. The Definition of Done requires it.

## Known gaps

- No end-to-end or browser tests. Auth0 login, the Vite proxy to the backend, and the real Postgres and MinIO services are only exercised by hand.
- CI runs the backend suite on SQLite because no `SQL_ENGINE` is set there, while local runs use Postgres in the container. Both pass today, but Postgres-specific behavior is not checked in CI.
- No coverage threshold is enforced.
- Frontend tests cover 6 of the 26 components.
