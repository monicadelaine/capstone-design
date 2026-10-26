# Iteration 2 Demo Script (2 minutes)

Run from the repository root on the demo laptop. Everything below is on `main`.

## Before class (10 minutes, do it the night before or an hour early)

1. Start Docker Desktop. If macOS asks for your password ("privileged port mapping"), enter it, or Docker never starts.
2. Start the stack and load demo data:
   ```
   git pull
   docker compose -f docker-compose.dev.yml up --build -d
   docker compose -f docker-compose.dev.yml exec backend python manage.py migrate
   docker compose -f docker-compose.dev.yml exec backend python manage.py seed_demo
   ```
   `seed_demo` prints: `Fall 2026: 5 sponsors, 16 projects, 20 students ...`. Re-running it is safe.
3. Install the solver once, outside Docker:
   ```
   python3 -m venv ~/ortools-venv && ~/ortools-venv/bin/pip install ortools
   ```
4. Open http://localhost:5173 and log in with your crimson account once, so the login is warm. Your account must exist as a Student row (it does on Margulan's machine). Leave the tab on the student home page.
5. For the fallback in step 2, create a local admin login if you don't have one: `docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser`.

## The demo

| # | Time | Do | Say |
|---|---|---|---|
| 1 | 0:30 | `~/ortools-venv/bin/python docs/investigations/or-tools/assign.py 100 25` | "This is the sponsor's request from September. 100 students, 25 projects of 4. It finds the best assignment in under a tenth of a second and proves nothing better exists. 62 get their first choice." |
| 2 | 0:45 | Browser: Submit preferences. Pick 5 high, 5 medium, 5 low from the 16 projects. Save. The home page shows your top choices. | "This is the ranking form, finished this iteration. The deadline is now enforced on the server, not just hidden in the browser." |
| 3 | 0:30 | New tab: http://localhost:8000/api/v1/preferences/ shows 403. Then `docker compose -f docker-compose.dev.yml exec backend pytest project/tests/test_views.py -k "Ownership or AssignmentAccess" -q` | "Before, any logged-in user could read every student's choices. Now a student only sees their own, and these tests prove it." |
| 4 | 0:15 | `scripts/test.sh` (or just point at the green check on GitHub Actions) | "240 backend and 36 frontend tests, run on every pull request." |

## If something breaks

- **Login fails (Auth0):** skip the form. Open http://localhost:8000/admin, log in with the local admin from step 5, and show Preferences: 300 ranked rows from 20 students.
- **Docker won't start:** do step 1 (it needs no Docker), then run the backend tests without Docker as in [docs/testing/README.md](../../../docs/testing/README.md), and show the GitHub Actions page.
- **Solver not installed:** show the results table in [docs/investigations/or-tools-evaluation.md](../../../docs/investigations/or-tools-evaluation.md).

## What was verified on 2026-10-26

- Backend on a fresh database: migrations, `seed_demo` twice, and the API returning 403 without a login for semesters, preferences, assignments, projects, and email. Backend suite: 240 passed.
- Solver script output as above.
- **Not verified:** the logged-in browser flow in step 2, because it needs a real Auth0 login, and Docker could not start overnight (it was waiting for the macOS password). Rehearse step 2 once before class.
