# FAQ

**Audience:** whoever inherits the project, the instructor, and developers. Short answers, each pointing to the page that explains it in full.

Written 2026-11-20. Students and sponsors have their own questions and answers at the end of the [user guide](../user-guide/README.md#faq-and-troubleshooting).

| I am... | Start at |
|---|---|
| Taking over the project | [Handoff](#handoff) |
| The instructor | [How do I...](#how-do-i-for-the-instructor) |
| A developer with an error on my screen | [Common errors and fixes](#common-errors-and-fixes) |
| A developer new to the code | [Questions from developers](#questions-from-developers) |

## Handoff

### Who owns each account?

Rows marked **to confirm** are not recorded anywhere in the repository. They have to be filled in by the person named before the team leaves; until then, treat that account as at risk.

| Account | What it is for | Owner today | After handoff it should be |
|---|---|---|---|
| GitHub repository `monicadelaine/capstone-design` | The code, issues, project board, CI | Dr. Anderson Herzog's account | Unchanged. Remove the four team members as collaborators when they are no longer needed |
| Auth0 tenant `dev-hx43g1ojtwfadqxq.us.auth0.com` | Student and sponsor login | Created by Margulan Baizhakyp on 2026-10-26 (#45). **To confirm:** whether the instructor has been added as a tenant admin | The instructor as tenant admin, students removed |
| Google Cloud project and its billing | The VM the site runs on, and the storage bucket | Set up by Noland Miller (PR #59). **To confirm:** project ID, billing account, who else has access | Owned or co-owned by the instructor or the department |
| DuckDNS subdomain `ua-capstone-design` | The site's address | **To confirm** (Noland Miller) | An account the instructor can log in to, or a university domain |
| Sending email account | Emails to sponsors and students | A course-named Gmail account was used for testing ([investigation](../investigations/mailhog-to-smtp2go.md)). **To confirm:** who controls it, and what the live site uses | A mailbox the instructor controls |
| Django admin superuser on the live site | The instructor's tools | **To confirm:** which accounts exist | One account per instructor; team members' accounts deactivated |

Why this table matters: the previous team's cloud project and domain were under personal accounts, and both were gone when this team started ([ADR-001](../decisions/ADR-001-stack.md)).

### Where are the secrets?

None are in the repository. All of them are in three files on the VM, in the folder where the repository is checked out. [Configuration](../deployment-guide/configuration.md) describes every line.

| Secret | Where it lives | How to change it |
|---|---|---|
| Django `SECRET_KEY` | `.env.production` on the VM | Edit the file, then recreate the backend. Every admin is logged out and any team proposal waiting for approval has to be proposed again |
| Database password | `.env.production` and `.env.production.db` on the VM, and inside the database | Three places have to change together: [Operations: change the database password](../deployment-guide/operations.md#change-the-database-password) |
| SMTP password | `.env.production` on the VM | Create a new one at the mail provider, edit the file, recreate the backend |
| Auth0 logins | The Auth0 dashboard; nothing on the server | The Auth0 domain and client ID in the env files are public values, not secrets. The application has no client secret |
| Instructor's admin password | The database (hashed) | `python manage.py changepassword <username>`: [Operations: accounts](../deployment-guide/operations.md#accounts) |
| Google Cloud Storage access | No key file. The VM's own service account | Managed in the Google Cloud console under IAM |

After changing anything in `.env.production`, a restart is not enough: [Configuration: changing a setting](../deployment-guide/configuration.md#changing-a-setting).

The three files exist only on the VM. Keep a copy in the instructor's password manager, or they are lost with the VM.

### Who do I contact?

| For | Person | GitHub |
|---|---|---|
| The product, requirements, and all final decisions | Dr. Monica Anderson Herzog, sponsor and instructor | `monicadelaine` |
| Deployment, the VM, Google Cloud | Noland Miller | `nrmiller4` |
| Auth0 and login | Margulan Baizhakyp | `mbaizhakyp` |
| Student and sponsor screens, emails, roster import, attachments, user guide | Jayden White | `jtwhite18` |
| Team assignment and the solver, project review, development and deployment guides | Gaurav Shrivastava | `GauravS11112003` |

The team is the Fall 2026 CS 495 group. After the semester, open an issue on the repository rather than relying on anyone answering.

### Where do I start?

1. Read [Recommendations](../recommendations/README.md). Its first section is what to do before a real class uses the site.
2. Run the project on your own machine: [development guide](../development-guide/README.md).
3. Read [the architecture page](../development-guide/architecture.md) before changing code.
4. Before relying on the live site, read [what is deployed today](../deployment-guide/README.md#what-is-deployed-today).

### Is it finished?

The full semester works: sponsors submit, the instructor reviews, imports the roster, students rank, teams are proposed, adjusted and approved, and students and sponsors see their teams. What is not done is listed in [Recommendations](../recommendations/README.md) and, for security, in the [security assessment](../security/README.md#open-findings).

## How do I... (for the instructor)

Step-by-step instructions with screenshots are in the [instructor guide](../user-guide/README.md#instructor-guide). These are the questions that come up most.

### Why can't a student log in?

Almost always because their email is not on the roster. A student is recognised by their `@crimson.ua.edu` address being in **Students**, spelled exactly as they signed up with it. Add or correct it and ask them to log in again. The other cause is an unverified email: they have to click the link Auth0 sent them. See [Import the class roster](../user-guide/README.md#3-import-the-class-roster).

### How do I re-import the roster?

Import the new file the same way as the first. Students already there are matched by CWID and updated, new ones are added, and rows with problems are listed with their row number and skipped. **An import never removes anyone.** Delete students who dropped, and last semester's students, by hand in **Students**. See [Import the class roster](../user-guide/README.md#3-import-the-class-roster).

### The roster file is refused. Why?

The file has to be saved as "CSV UTF-8 (Comma delimited)", not plain CSV, and has to contain the expected column names. The page says which of the two it is. Background: [roster import investigation](../investigations/blackboard-csv-import.md).

### The students don't divide evenly into teams. What do I do?

Lower **Minimum team size** on the semester. With 22 students and a team size of 4, a minimum of 3 lets the site build teams of 3 and 4. If the message says the settings cannot work, there are too few or too many seats: change the sizes or add projects. See [Set up a semester](../user-guide/README.md#1-set-up-a-semester).

### What does "approving" assignments do?

Proposing saves nothing; it only shows you teams. You can move students and propose again as often as you like. Approving is the step that saves the teams, makes them visible to students and sponsors, and emails each student whose placement is new or changed. A proposal is valid for one hour; after that, propose again. See [Build and publish teams](../user-guide/README.md#5-build-and-publish-teams).

### Can I change teams after approving?

Yes. Propose again, move students, and approve; only students whose project changed are emailed. Or edit a single assignment under **Assignments**.

### How does the site decide the teams?

It gives every student exactly one project and keeps every team within the size limits, then picks, out of all arrangements that do that, the one where students' rankings are satisfied best overall. It is not random and not first-come-first-served. Details: [main flows](../development-guide/flows.md) and the [solver evaluation](../investigations/or-tools-evaluation.md).

### Why didn't students get the reminder email?

The reminder only goes out if the server is set up to send it daily, and only to students who have saved no rankings. See [Operations: deadline reminders](../deployment-guide/operations.md#deadline-reminders).

### A sponsor's project is not showing to students. Why?

A new project is **Pending** until you approve it, and approving puts it in the semester. See [Review submitted projects](../user-guide/README.md#2-review-submitted-projects).

### I don't see an action, such as "Propose assignments".

Your admin account lacks the permission for it. A superuser can grant it under **Users**. The first account created on a server is a superuser and sees everything.

### How do I give another instructor or a TA access?

Create a staff account for them in Django admin: [Operations: accounts](../deployment-guide/operations.md#accounts). They do not need an Auth0 account.

## Common errors and fixes

Problems this team actually hit, with the cause and the fix. For errors on the production server, the [troubleshooting table](../deployment-guide/operations.md#troubleshooting) is longer.

### On a developer's machine

| What you see | Cause | Fix |
|---|---|---|
| The backend container exits with `permission denied` on `entrypoint.sh` (macOS, Linux) | The script lost its executable bit, and the dev stack mounts the folder over the image | `chmod +x backend/entrypoint.sh`. Fixed in the repository by PR #32; see [known platform issue](../development-guide/README.md#known-platform-issue) |
| Compose refuses to start, or the backend crashes with `invalid literal for int()` naming a line of your env file | Two settings ended up on one line of `.env.dev`, for example `DEADLINE_REMINDER_DAYS=3APP_URL=...` | Put each setting on its own line |
| Login fails with "Client ... is not authorized to access resource server" | In a new Auth0 tenant, the application is not authorized for the API | [Auth0 setup](../development-guide/auth0-setup.md), step 3 |
| After login: "Authentication Error: No role found in your account" | The token has no roles. The Auth0 tenant is missing the post-login Action, or your env files point at the wrong tenant | Check the three `AUTH0_*` values against `.env.example`; [Auth0 setup](../development-guide/auth0-setup.md), step 4 |
| The site does not show your change | The containers are running an old build | `docker compose -f docker-compose.dev.yml up --build -d` |
| Tests fail after you changed a model | A migration is missing | `python manage.py makemigrations`, commit the file, run the tests again: [conventions](../development-guide/conventions.md#migrations-and-models) |
| Your new migration has the same number as one on `main` | Someone merged a migration while you worked | Merge `main` into your branch, delete your migration, and generate it again |
| Email tests fail only on your machine | Your `.env.dev` sets `ALLOW_STUDENT_EMAILS=True` or a real SMTP server | The tests now set these themselves; pull `main`. Keep Mailhog as your default |
| `git status` shows a file like `.~env.dev` | An editor's backup copy of your env file, which `.gitignore` does not cover | Delete it. Never `git add -A` without reading the list; that file holds passwords |
| A fresh clone will not start: MinIO images cannot be pulled, or a shell script fails on Windows with `\r` errors | Outdated image tags, and Windows line endings in shell scripts | Pull `main`; the images are pinned and line endings are enforced (PR #27) |

### On the live site

| What you see | Cause | Fix |
|---|---|---|
| The page freezes after logging in | A logged-in user with no role was redirected in a loop. Fixed in PR #60; a site still doing this is running an old build | Redeploy: [deploy a new version](../deployment-guide/operations.md#deploy-a-new-version) |
| The live site is missing features that are on `main` | Nothing deploys automatically | Same |
| Uploading a file fails with 413 | A proxy's size limit. nginx was limiting uploads to 1 MB until PR #93 raised it to 30 MB | Redeploy; if it persists, check the Caddyfile |
| The backend restarts forever on a new server, with `PermissionError ... staticfiles` | The static files folder belonged to root. Fixed in PR #115 | Pull and rebuild |
| Login works on a laptop but not on the live site | The site's address is not in the Auth0 application's allowed URLs, or the server's env files name a different tenant | [Configuration: Auth0](../deployment-guide/configuration.md#auth0), #58 |

## Questions from developers

### How do I run it?

[Development guide](../development-guide/README.md). You need Docker and Git, nothing else.

### How do I run the tests?

`scripts/test.sh` runs both suites; the stack has to be up first. [Testing](../testing/README.md).

### Where is the code for a feature?

[Main flows](../development-guide/flows.md) lists, for each feature, the files that do the work.

### How do I add a field, an endpoint, or a screen?

[Adding a feature](../development-guide/adding-a-feature.md) is a worked example of all three, with tests.

### Why Auth0? Why not rebuild it? Why this solver?

Each has a short record of what was considered: [ADR-001](../decisions/ADR-001-stack.md) (keep the existing code), [ADR-002](../decisions/ADR-002-auth.md) (keep Auth0), [solver evaluation](../investigations/or-tools-evaluation.md). The full list of things decided against is in [Recommendations](../recommendations/README.md#6-considered-and-decided-against).

### Why does the instructor use Django admin and not the Vue app?

The instructor's tools were built as Django admin pages and actions, which gave tested tools sooner than new screens would have. Students and sponsors use the Vue app. [Architecture](../development-guide/architecture.md).

### How do I make myself an admin locally?

For Django admin: `docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser`. For the admin role on the API, assign the `admin` role to your user in the Auth0 dashboard: [Auth0 setup](../development-guide/auth0-setup.md), step 5.

### How do I get sample data?

`docker compose -f docker-compose.dev.yml exec backend python manage.py seed_demo` creates a semester, sponsors, projects, and students with rankings. Local use only; never on the live site.

### Is it safe to put the Auth0 domain and client ID in Git?

Yes. Every visitor's browser receives them. Never commit a client secret, a Management API token, or any `.env` file other than the three examples.

### Where did the previous team's work go?

It is the base of this code. What it was and what was wrong with it is in the [v1 reference](../investigations/v1-reference.md). Their own documents are kept in [investigations/v1/](../investigations/v1/README.md) as a record; they describe a setup that no longer exists, so use the [deployment guide](../deployment-guide/README.md).
