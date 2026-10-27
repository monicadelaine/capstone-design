# Capstone Design Manager

A web platform for the University of Alabama Computer Science senior design course. Sponsors submit projects, students rank their choices, and the instructor assigns teams, in one place instead of email and spreadsheets.

**Sponsor:** Dr. Monica Anderson Herzog, Department of Computer Science, The University of Alabama
**Team (CS 495, Fall 2026):** Gaurav Shrivastava, Jayden White, Margulan Baizhakyp, Noland Miller

## Status

**Iteration 2 (due 2026-10-27).** Deployed on Google Cloud at https://ua-capstone-design.duckdns.org/. Students rank projects; sponsors submit projects; the API limits each user to their own data; the instructor can have OR-Tools propose an assignment of students to projects and approve it in Django admin. Review: [course/iterations/iteration-2/review.md](course/iterations/iteration-2/review.md).

Remaining work for Iteration 3 and handoff is the Product Backlog view on the board below.

## Links

- **GitHub Project board (backlog, iteration plans, results):** https://github.com/users/mbaizhakyp/projects/1. It is owned by a team member's account, so it does not appear under this repository's Projects tab; the Senior Design Project linked there is the course example.
- **Documentation:** [docs/](docs/) — [development guide](docs/development-guide/), [data model](docs/development-guide/data-model.md), [decisions](docs/decisions/), [v1 reference](docs/investigations/v1-reference.md)
- **Course records:** [course/](course/) — presentations, iteration reviews and retrospectives
- **Stand-ups:** [Issues labeled `stand-up`](https://github.com/monicadelaine/capstone-design/issues?q=label%3Astand-up), indexed by date in [course/](course/README.md#stand-ups)
- **Prior team's repository (reference only):** https://github.com/jmburke4/capstone-design-manager

## Run it locally

Requires Docker Desktop and Git. Full steps in the [development guide](docs/development-guide/README.md).

```
cp .env.example .env.dev
cp .env.example.db .env.dev.db
cp frontend/.env.example.local frontend/.env.dev.local
# edit the three files; see the development guide for values
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate --noinput
```

| Service | Address |
|---|---|
| Website | http://localhost:5173 |
| Django admin | http://localhost:8000/admin/ |
| Mailhog (email) | http://localhost:8025 |
| MinIO console (files) | http://localhost:9001 |

Tests: `scripts/test.sh` on macOS, Linux, or Git Bash, or `.\scripts\test.ps1` in PowerShell, runs both suites. Details in [docs/testing/](docs/testing/).

## How we work

One Issue per piece of work, labeled by type. Code changes go on a branch and through a pull request with CI green and one teammate's review. Documentation changes may be committed to `main` directly. An Issue moves to Done only when it meets the [Definition of Done](docs/definition-of-done.md). Three stand-ups a week as GitHub Issues. Details in the [development guide](docs/development-guide/README.md#start-your-work-on-a-branch).

## Technology

Vue 3 + Vite frontend, Django REST Framework backend, PostgreSQL, Auth0 for login, MinIO/S3 for file storage, Docker Compose for development. See [docs/decisions/](docs/decisions/) for why.
