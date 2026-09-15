# v1 Reference: Prior Team's Capstone Design Manager

**Purpose:** what the Spring 2026 team built, what it actually does, and what to reuse or avoid. Written for the Fall 2026 team as a requirements and lessons-learned reference. Not a spec for our system.

**Sources**
- Prior repo: https://github.com/jmburke4/capstone-design-manager (branches `main`, `Cloud-V2`, `docs`; last push 2026-04-23)
- Prior site: https://jmburke4.github.io/capstone-design-manager/
- Prior production: https://ua-capstone-projects.com (GCP VM, may be down)
- Our copy of their `main` branch: this repo's `backend/` and `frontend/` as of the initial commit
- Their `userguide.pdf`, deployment doc, and READMEs

File:line pointers below refer to our copy of their `main`.

---

## 1. What v1 is

A web app for the UA CS senior design course. Sponsors submit projects, students rank them, the instructor assigns students to projects in the Django admin, and emails go out to sponsors. Stack: Vue 3 + Vite frontend, Django REST Framework backend, PostgreSQL, Auth0 login, MinIO/S3 for files, Mailhog for dev email, Docker Compose. Production ran on one GCP Compute Engine VM behind Nginx with Let's Encrypt.

Prior team: 5 students (jmburke4 91 commits, chm423 37, cole-w-kelley 33, tehicks1 19, MrGermanDude 17). 58 PRs, 34 Issues.

---

## 2. Roles and workflow (the requirements we inherit)

**Roles:** student, sponsor, admin. Roles are not stored in the database. They live in an Auth0 token claim (`https://backend-api-capstone/roles`) and both frontend and backend read `roles[0]`.

**How users get in**
- Students: admin imports a Blackboard CSV into the Student table (columns `EMAIL, FIRST_NAME, MIDDLE_NAME, LAST_NAME, PREF_NAME, CWID, STU_CLASS_CODE, MAJR_1_CODE`). A student then signs up with a `@crimson.ua.edu` email. If the email isn't in the table, they see "not registered" and can only log out.
- Sponsors: self sign-up, email/password or social login. Social logins are auto-assigned sponsor.
- Admin: an Auth0 Role named `admin` assigned by hand, plus a separate Django superuser for `/admin/`.

**Semester workflow, in order**
1. Admin creates a `Semester` (Fall/Spring/Summer + year) with an `assignment_date`. That date is the student preference deadline.
2. Admin emails sponsors (outreach email) to solicit projects.
3. Sponsors submit projects via the app. Projects start as `Pending`.
4. Admin adds projects to the semester in Django admin. Only then do students see them.
5. Students rank projects: exactly 5 High, 5 Medium, 5 Low, so 15 preferences each. Ties within a tier are unordered. The deadline is enforced only in the browser.
6. Admin assigns manually in Django admin: filter Preferences by semester/project/rank, select rows, pick a project. One assignment per student per semester. **There is no matching algorithm**, despite the user guide claiming one.
7. Admin changes project status by hand (`Pending`, `In Progress`, `Complete`, `Cancelled`). Nothing changes it automatically.
8. Sponsors can submit free-text feedback tied to a project and semester.

**Emails that exist:** sponsor outreach, project presentation invite (one per project). Both sent from Django admin actions or exported as `.eml` files to send from a personal mail client. **No emails to students. No assignment notification. No deadline reminder.**

---

## 3. Data model

| Model | Key fields | Notes |
|---|---|---|
| `Sponsor` | first/last name, email, organization, phone, `projects_allowed` (default 3) | email not unique; `projects_allowed` enforced only client-side |
| `Student` | `cwid` (8 digits, unique), first/middle/last/preferred name, email, description, class_code, major_code | email not unique; "description" is skills text from the ranking form |
| `Project` | name, description, sponsor FK, sponsor_availability, status, website | unique on (name, sponsor); status read-only via API |
| `Semester` | semester enum, year, `assignment_date`, M2M projects | unique on (semester, year) |
| `Preference` | student FK, project FK, rank (1/2/3), semester FK | PK is slug `student-project`; semester auto-derived from save date |
| `Assignment` | semester, student, project | PK is slug `student-semester`, so one per student per semester |
| `Attachment` | project FK (nullable), file or link or `content` | 25 MB max; pdf/docx/pptx/png/jpg/jpeg/zip; also used to store exported emails |
| `Feedback` | sponsor, project, semester, text | free text only |

No custom Django user model. No `role` column. No `Team` model: a "team" is just every student assigned to the same project in a semester.

Source: `backend/user/models.py`, `backend/project/models.py`. ERD: `backend/erd.uxf`.

---

## 4. API surface

Base path `/api/v1/`. Auth is a Bearer JWT from Auth0 validated against the tenant's JWKS. No pagination anywhere.

| Resource | Endpoints | Auth |
|---|---|---|
| projects | CRUD `/projects/`; list is filtered to current semester | required |
| attachments | CRUD `/attachments/`, `/attachments/{id}/download/` | required |
| semesters | CRUD `/semesters/`, `/semesters/current` | **none** |
| assignments | CRUD `/assignments/` | required |
| feedback | CRUD `/feedback/` | required |
| preferences | GET all, POST single or bulk, PATCH bulk, DELETE `/preferences/{student}-{project}/` | required |
| sponsors / students | CRUD, `/sponsors/{id}/projects/` | required |
| profile | GET/POST/PUT `/profile/` by token email; students get 403 on PUT | required |
| emails | `/emails/send`, `/emails/sponsor-outreach`, `/emails/project-presentation` | **none** |

**Critical:** the only permission check anywhere is "is authenticated." No endpoint checks role. Any student token can edit any project, create assignments, or delete another student's preferences. `GET /preferences/` and `GET /assignments/` return every row for every student and the browser filters to "mine."

Source: `backend/project/urls.py`, `backend/user/urls.py`, `backend/emails/urls.py`, `backend/project/views.py`.

---

## 5. Frontend pages

| Route | Who | What |
|---|---|---|
| `/` | public | login, signup as student or sponsor |
| `/student` | student | dashboard: top 5 preferences, assignment if past deadline |
| `/student/projects` | student | project gallery |
| `/student/submit` | student | ranking form (5/5/5), hidden after deadline |
| `/student/assignment` | student | assigned project |
| `/sponsor` | sponsor | dashboard |
| `/sponsor/submit`, `/sponsor/edit`, `/sponsor/feedback` | sponsor | project forms |
| `/projects/:id` | any logged-in | project detail |
| `/profile/create`, `/profile/edit` | any; students can't edit | profile |

No admin UI in the Vue app. Everything admin happens in Django admin at `/admin/`. Six admin-panel components exist in the source but are unrouted and dead.

Source: `frontend/src/router/index.js`, `frontend/src/components/Sidebar.vue`.

---

## 6. Auth0 setup (the part that lives outside the code)

The role is passed at signup as a fake OAuth scope, `role:student` or `role:sponsor` (`frontend/src/components/Login.vue:55`). Two Auth0 Actions read it. Their source is on the `Cloud-V2` branch under `Auth0-Scripts/`, not on `main`:

- **Pre User Registration** (`ValidateRole&Domain`): rejects student signups not ending in `@crimson.ua.edu`; sets `app_metadata.role`; denies signup with no role hint.
- **Post Login** (`AssignRole&EnforceAccess`): first-time social logins become sponsor; denies unverified email; adds `email` and `roles` claims under namespace `https://backend-api-capstone/`; merges Auth0-assigned roles like `admin`.

The prior README admits this is fragile: "It is highly likely that the current implementation is vulnerable to role spoofing/privilege escalation" (`README.md:115`). The role hint is client-controlled.

Their dev tenant, client ID, and audience are committed in `README.md:63-79`. Do not reuse them. Make our own tenant.

Their README also notes: no MySSO, no "resend verification email," and Auth0 verification links expire after 7 days.

---

## 7. Config and deployment

**Env files (dev):** `.env.dev` (backend, MinIO), `.env.dev.db` (Postgres), `frontend/.env.dev.local` (three `VITE_AUTH0_*` vars). Their docs call consolidating these a backlog item. The `env.example` files their README references are not in `main`.

**Required env vars:** `SECRET_KEY`, `DEBUG`, `DJANGO_ALLOWED_HOSTS`, `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `SQL_*` (5 vars), `DATABASE=postgres`, `AWS_*` and `MINIO_*` for storage, `EMAIL_*` for SMTP. Backend crashes at import if `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, or `DJANGO_ALLOWED_HOSTS` are unset.

**Docker Compose (dev):** backend :8000, frontend :5173, postgres:17, mailhog :1025/:8025, minio :9000/:9001, minio-bootstrap.

**Production (Cloud-V2 branch only, never merged):** GCP Compute Engine VM `capstone-prod-vm` in `us-central1-b`, project `capstone-design-app-prod`. Domain via Google Cloud Domains + Cloud DNS. Nginx serves the built Vue app and proxies the API. Certbot for TLS. Scripts `01-create-vm.sh` through `04-setup-ssl.sh` plus `generate-secrets.sh`. Ran on $50 of GCP education credits. Their doc says the deploy script "has historically been the most error-prone."

`Cloud-V2` is 30 commits ahead of `main` and includes: `DEPLOYMENT_README.md`, `docker-compose.prod.yml`, `nginx/`, `scripts/`, `Dockerfile.prod`, `gunicorn.conf.py`, `health.py`, admin middleware, and the Auth0 scripts. If we want any of that, fetch it from the prior repo's `Cloud-V2` branch.

CORS and CSRF origins are hardcoded to localhost in `backend/core/settings.py:172-179`.

---

## 8. Tests

**Backend:** pytest + pytest-django, ~3,000 lines across `project/tests`, `user/tests`, `emails/tests`. Cover models, serializers, views, admin actions. Require a real PostgreSQL plus `AUTH0_*` and `DJANGO_ALLOWED_HOSTS` env vars, so they only run inside the Compose stack:

```
docker compose -f docker-compose.dev.yml exec backend pytest
```

Not covered: Auth0 authentication class, profile view, semester viewset, storage.

**Frontend:** vitest + @vue/test-utils, 8 files. Cover the api service, both Pinia stores, Sidebar, ConfirmationModal, and three dead components. The ranking form, the most complex logic in the app, has no tests.

**CI:** their one CI PR (#28) was closed unmerged. They never had CI running. The `test.yml` workflow in our repo is unrelated to v1 and currently fails because it looks for `requirements.txt` at the root.

---

## 9. Dependencies

Backend `requirements.txt` pins **nothing** (line 1: `# TODO Pick package versions to use [#3]`). Python 3.11 in the Dockerfile. Django was 5.2 or 6.0 depending on build date. Postgres 17. Frontend: Vue 3.5, Vite 7, Pinia 3, vue-router 4.6, axios 1.13, @auth0/auth0-vue 2.5, vitest 4; Node 24. `tabulator-tables` is a dependency used only by dead components.

---

## 10. Known gaps, ranked by how much they matter to us

**Security and correctness**
1. No role-based authorization on any API endpoint.
2. `/semesters/` CRUD and all three `/emails/*` endpoints require no auth at all. The email endpoints are an open mail relay.
3. Role assignment at signup is client-controlled and spoofable.
4. Preference deadline enforced only in the browser.
5. All students' preferences and assignments are sent to every student's browser.
6. JWKS fetched over the network on every request; JWT algorithm read from the untrusted token header.
7. A DEBUG button in `App.vue` dumps the full Auth0 user object, always visible.
8. Admin email forms accept an SMTP password in a plaintext POST body.

**Missing features the sponsor probably expects**
9. No matching algorithm. Assignment is row-by-row in Django admin.
10. No student-facing emails or notifications of any kind.
11. No admin UI outside Django admin; the four admin dashboard buttons link to a route that doesn't exist.
12. Sponsors have no file upload UI and no view of their assigned students.
13. No way to resend an Auth0 verification email.
14. No team concept; no team size limits; no per-project capacity.

**Engineering debt**
15. Unpinned dependencies (their open Issue #3).
16. Cloud config never merged to main; three env files with duplicated values.
17. Hardcoded year 2025 in email subject (`emails/utils.py:78`); hardcoded localhost CORS.
18. Duplicate project names allowed (their open Issue #34); serializer fields never audited (their open Issue #26).
19. Dead code: two unrouted email export views, an unmounted email admin site, six orphan Vue components, unused `.txt` email templates.
20. Bugs in the ranking form: a Ref tested as a boolean (`StudentRankForm.vue:216`), instructions shown only after the deadline (`:289`), profile save always 403s and is swallowed (`:183`).

**Doc contradictions.** Their user guide claims automated assignment, top-3 ranking, sponsor uploads, and Cloud Run hosting. None of that matches the code. Treat their code, not their docs, as the truth about v1.

---

## 11. What the prior team's process shows

- They worked on feature branches with PRs (58 of them) and Issues for features. That's the pattern our course expects.
- Their last three weeks (April 2026) were "finalization," "polish," and "fix" PRs. Attachments were "backlogged for next group" (PR #55 comment).
- Open Issues they left: #34 duplicate project names, #31 attachments, #26 serializer audit, #12 assignment string formatting, #3 pin dependency versions.
- Their commit history has no tags, so there's no way to check out an "as submitted" state.

---

## 12. What to take, what to leave

**Take, regardless of stack**
- The role list and the semester workflow in section 2. This came from the same sponsor and is the closest thing to a requirements doc we have.
- The data model shape in section 3, minus its mistakes: add role to the user record, add uniqueness on email, make status derived from assignment state, add a team/capacity concept.
- The Blackboard CSV column list for student import.
- The 5/5/5 ranking rule as a starting point to confirm with the sponsor.
- The gap list in section 10 as acceptance criteria: each one is something we should get right.
- Their Auth0 Action scripts as an example of what not to do with role assignment.

**Leave**
- Their Auth0 tenant and client ID.
- The unrouted admin components, the email export views, the `.txt` templates.
- Their deploy scripts unless we choose the same VM-plus-Nginx setup; even then, fetch them from `Cloud-V2` and read before running.
- Their docs as a description of behavior.

**Decide, and write as an ADR in `docs/decisions/`**
- Keep Vue + Django + Postgres, or pick a new stack. If we keep it, we fork and fix; if not, we rebuild against the requirements above.
- Auth: Auth0 again, UA MySSO, or something simpler. Role assignment must be server-side either way.
- Hosting: GCP VM again (their credits are gone), or something with a free tier for students.
