# Capstone Design Manager

A web platform for the University of Alabama Computer Science senior design course. Sponsors submit projects, students rank their choices, and the instructor assigns teams, in one place instead of email and spreadsheets.

**Sponsor:** Dr. Monica Anderson Herzog, Department of Computer Science, The University of Alabama
**Team (CS 495, Fall 2026):** Gaurav Shrivastava, Jayden White, Margulan Baizhakyp, Noland Miller

## Status

**Iteration 1 (due 2026-09-24).** We are building on the Spring 2026 team's codebase ([ADR-001](docs/decisions/ADR-001-stack.md)). The full stack runs locally with Docker Compose and the backend test suite passes in CI. Not yet deployed; hosting is under investigation. No new user-facing features are live yet.

Delivered so far: local development environment and guide, CI, architecture decisions, data model, project board and backlog.

## Links

- **GitHub Project board:** https://github.com/users/mbaizhakyp/projects/1
- **Documentation:** [docs/](docs/) — [development guide](docs/development-guide/), [data model](docs/development-guide/data-model.md), [decisions](docs/decisions/), [v1 reference](docs/investigations/v1-reference.md)
- **Course records:** [course/](course/) — presentations, iteration reviews and retrospectives
- **Stand-ups:** [Issues labeled `stand-up`](https://github.com/monicadelaine/capstone-design/issues?q=label%3Astand-up)
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

Tests: `docker compose -f docker-compose.dev.yml exec backend pytest -q`

## How we work

One Issue per piece of work, labeled by type. Code changes go on a branch and through a pull request with CI green and one teammate's review. Documentation changes may be committed to `main` directly. Three stand-ups a week as GitHub Issues. Details in the [development guide](docs/development-guide/README.md#start-your-work-on-a-branch).

## Technology

Vue 3 + Vite frontend, Django REST Framework backend, PostgreSQL, Auth0 for login, MinIO/S3 for file storage, Docker Compose for development. See [docs/decisions/](docs/decisions/) for why.
