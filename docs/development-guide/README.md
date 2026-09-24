# Development Guide

**Audience:** developers on the team. How to run the project locally and how we use branches and pull requests.

Originally written by Noland Miller as *CS 495 Website Deployment Directions* (Word). Converted to Markdown here so it is versioned with the code. Commands are shown for PowerShell; on macOS or Linux use `cp` instead of `Copy-Item` and forward slashes.


Repository: https://github.com/monicadelaine/capstone-design

You can start working on the project now. The Google Cloud deployment does not need to be finished first. You can clone the repository, run the website locally, create your own branch, make changes, and open pull requests.


## What you need

Git installed and signed in to GitHub.

Docker Desktop installed and running.

VS Code or another code editor.

Write/collaborator access to the professor-owned GitHub repository.

You will work from your own local copy of the project. You do not need to connect to anyone else's computer or Docker setup. GitHub is the shared source of truth for the code.


## Clone the project

Open PowerShell and clone the repository into a normal projects folder:

```
cd $HOME
mkdir Projects -ErrorAction SilentlyContinue
cd Projects
git clone https://github.com/monicadelaine/capstone-design.git
cd capstone-design
git status
```
You should be on the `main` branch with a clean working tree. If GitHub gives you a permission error, make sure you have access to the repository.


## Create your local environment files

The real `.env` files are not stored in GitHub because they can contain passwords and secrets. Copy the safe templates that are already in the repository:

```
Copy-Item .env.example .env.dev
Copy-Item .env.example.db .env.dev.db
Copy-Item frontend\.env.example.local frontend\.env.dev.local
```

**Backend: .env.dev**

Open `.env.dev` and use these local-development values:

```
SECRET_KEY=local-dev-secret-key
DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 backend

SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=capstone
SQL_USER=capstone
SQL_PASSWORD=capstone_dev_password
SQL_HOST=db
SQL_PORT=5432

AUTH0_DOMAIN=dev-qjyd077ykn3qqq7v.us.auth0.com   # prior team's tenant; to be replaced per ADR-002
AUTH0_CLIENT_ID=WMPr5zJLNFI0j9A8iUymDfAsP2mUXsn3
AUTH0_AUDIENCE=https://backend-api-capstone/

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=capstone-local
AWS_S3_ENDPOINT_URL=http://minio:9000
MINIO_ACCESS_URL=http://localhost:9000

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@example.com
EMAIL_FAIL_SILENTLY=False
```

**Database: .env.dev.db**

```
POSTGRES_DB=capstone
POSTGRES_USER=capstone
POSTGRES_PASSWORD=capstone_dev_password
```

**Frontend: frontend/.env.dev.local**

```
VITE_AUTH0_DOMAIN=dev-qjyd077ykn3qqq7v.us.auth0.com   # prior team's tenant; to be replaced per ADR-002
VITE_AUTH0_CLIENT_ID=WMPr5zJLNFI0j9A8iUymDfAsP2mUXsn3
VITE_AUTH0_AUDIENCE=https://backend-api-capstone/
```
Do not commit `.env.dev`, `.env.dev.db`, `frontend/.env.dev.local`, or any production `.env` file. The repository is already configured to ignore these files.


## Start the website locally

Open Docker Desktop and wait until Docker is running. Then, from the project root, run:

```
docker compose -f docker-compose.dev.yml up --build -d
```
Check that the containers started:

```
docker ps
```
You should see the frontend, backend, PostgreSQL database, MinIO, and Mailhog containers.

Run the database migrations:

```
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate --noinput
```
Run the Django system check:

```
docker compose -f docker-compose.dev.yml exec backend python manage.py check
```
Run the tests, both the backend and frontend suites:

```
scripts/test.sh
```
In PowerShell use `.\scripts\test.ps1` instead. At the current baseline both suites pass completely. The exact test counts will increase as we add more tests. See [docs/testing/](../testing/README.md) for running one suite or one file.


## Open the local site

If you need a local Django admin account, run:

```
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
```

## Start your work on a branch

Do not develop directly on `main`. Create a branch for each feature, fix, or setup change.

Before you start new work:

```
git checkout main
git pull origin main
```
Create a branch with a short, descriptive name:

```
git checkout -b feature/example-feature
```
Good examples are `feature/project-search`, `fix/login-redirect`, `docs/user-guide`, or `setup/deployment`.

Make your changes in VS Code. You can check what you changed at any time with:

```
git status
```
Before you push your branch, run the tests again:

```
scripts/test.sh
```
PowerShell: `.\scripts\test.ps1`
Then stage, commit, and push your work:

```
git add <files-you-changed>
git commit -m "Short description of the change"
git push -u origin feature/example-feature
```

## Open a pull request

Go to the GitHub repository and create a Pull Request. Use `main` as the base branch and your feature branch as the compare branch. Use a short title and explain what you changed and how you tested it.

Wait for the GitHub checks to finish. If a check fails, open the failed job, fix the problem on the same branch, commit the fix, and push again. The pull request updates automatically.

Only merge after the checks are green and any merge conflicts are resolved.


## After your pull request is merged

Update your local copy before you start another task:

```
git checkout main
git pull origin main
```
You can delete the old local feature branch after it is merged:

```
git branch -d feature/example-feature
```

## If main changes while you are working

You do not need to restart your work. Bring the newest `main` into your branch before you finish the pull request:

```
git fetch origin
git checkout feature/example-feature
git merge origin/main
```
If Git reports a merge conflict, resolve it carefully in VS Code, run the tests again, and then commit the conflict resolution.


## Stop and restart the local project

To stop the containers without deleting your local database/storage:

```
docker compose -f docker-compose.dev.yml down
```
To start them again later:

```
docker compose -f docker-compose.dev.yml up -d
```
Use `--build` if Dockerfiles, dependencies, or setup files changed:

```
docker compose -f docker-compose.dev.yml up --build -d
```
Warning: Do not use `docker compose down -v` unless you intentionally want to delete your local database and storage volumes.


## Common problems

Docker cannot connect: Open Docker Desktop and wait until the Docker engine is fully running.

An env file is missing: Make sure you are in the project root and that `.env.dev`, `.env.dev.db`, and `frontend/.env.dev.local` exist.

The website does not show your latest code: Run `docker compose -f docker-compose.dev.yml up --build -d` again.

Git push says permission denied: Make sure your GitHub account has write/collaborator access to the repository.

Tests fail after a model/database change: Check whether you need a Django migration, run the migration, and rerun the tests.

Your path contains `capstone-design\capstone-design`: You are probably one folder too deep. Go back one directory and run commands from the project root.


## Google Cloud and the shared website

You do not need Google Cloud to collaborate or make changes. You can already work locally and use GitHub branches and pull requests.

Google Cloud is being set up for the shared public version of the website. Until deployment automation is finished, merging a pull request into `main` will not automatically update the public Google Cloud site. Deployment is a separate step.


## Team workflow to follow

Pull `main` -> create a branch -> make one focused change -> test locally -> push -> open a PR -> wait for green checks -> merge -> pull `main` again.


## Local service addresses

| Service | Address |
|---|---|
| Main website | http://localhost:5173 |
| Django admin | http://localhost:8000/admin/ |
| Mailhog | http://localhost:8025 |
| MinIO console | http://localhost:9001 |

## Known platform issue

On macOS and Linux, `backend/entrypoint.sh` must be executable or the backend container exits with `permission denied`. The dev Compose file bind-mounts `backend/`, which overrides the `chmod` in the Dockerfile. Until the executable bit is committed, run `chmod +x backend/entrypoint.sh` once after cloning. Windows Docker mounts ignore file modes, so this does not occur there.
