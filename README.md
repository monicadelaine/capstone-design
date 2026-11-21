# Capstone Design Manager

A web platform for the University of Alabama Computer Science senior design course. Sponsors submit projects, students rank their choices, and the instructor assigns teams, in one place instead of email and spreadsheets.

**Sponsor:** Dr. Monica Anderson Herzog, Department of Computer Science, The University of Alabama
**Team (CS 495, Fall 2026):** Gaurav Shrivastava, Jayden White, Margulan Baizhakyp, Noland Miller

## Status

**Iteration 3, the final iteration (reviewed 2026-11-20).** One full semester runs end to end:

1. A sponsor submits a project, with files and links.
2. The instructor reviews it and approves it into a semester.
3. The instructor imports the class roster from Blackboard.
4. Students rank projects: five high, five medium, five low.
5. A solver (Google OR-Tools) proposes teams. The instructor can compare team sizes, move students, and approve.
6. Students and sponsors see their teams, and students are emailed.

Students and sponsors use the Vue app. The instructor works in the Django admin area. A deployment runs at https://ua-capstone-design.duckdns.org/; the [deployment guide](docs/deployment-guide/README.md) describes what is running there and how to bring it up to the current `main`.

Review: [course/iterations/iteration-3/review.md](course/iterations/iteration-3/review.md). What we would do next: [recommendations](docs/recommendations/README.md).

## Documentation

Everything is in [docs/](docs/). Start with the page for what you are doing:

| I want to... | Read |
|---|---|
| Use the site as a student, sponsor, or instructor | [User guide](docs/user-guide/README.md) |
| Run the project on my machine and change the code | [Development guide](docs/development-guide/README.md), then [architecture](docs/development-guide/architecture.md) |
| Host the site, deploy a new version, back it up | [Deployment guide](docs/deployment-guide/README.md) |
| Take over the project | [FAQ](docs/faq/README.md) and [recommendations](docs/recommendations/README.md) |
| Know what protects the data and what is still open | [Security assessment](docs/security/README.md) |
| Run or write tests | [Testing](docs/testing/README.md) |
| Understand why it is built this way | [Decisions](docs/decisions/README.md) and [investigations](docs/investigations/) |

## Links

- **GitHub Project board (backlog, iteration plans, results):** https://github.com/users/mbaizhakyp/projects/1. It is owned by a team member's account, so it does not appear under this repository's Projects tab; the Senior Design Project linked there is the course example.
- **Course records:** [course/](course/) — presentations, iteration reviews and retrospectives
- **Stand-ups:** [Issues labeled `stand-up`](https://github.com/monicadelaine/capstone-design/issues?q=label%3Astand-up), indexed by date in [course/](course/README.md#stand-ups)
- **Prior team's repository (reference only):** https://github.com/jmburke4/capstone-design-manager. Their documents are kept in [docs/investigations/v1/](docs/investigations/v1/README.md).

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

Vue 3 + Vite frontend, Django 5.2 with Django REST Framework, PostgreSQL, Auth0 for login, Google OR-Tools for team assignment, Docker Compose for development and production. Uploaded files go to MinIO in development and Google Cloud Storage in production. 496 backend and 75 frontend tests run in CI on every push. See [docs/decisions/](docs/decisions/) for why.
