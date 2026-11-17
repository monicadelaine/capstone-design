# Security: User roster write permissions

## Finding
`SponsorViewSet` and `StudentViewSet` previously used `IsAuthenticated` alone. Any
authenticated user could create, edit, or delete student and sponsor database
records through the general-purpose API, independently of the `/profile/` flow.

## Scope
Restrict unsafe HTTP methods on the two roster viewsets to Auth0 `admin` role
through the existing `AdminWriteOrReadOnly` permission class. Preserve
existing authenticated GET requests for compatibility with current frontend
flows. The `/profile/` endpoint is unchanged and still allows sponsors to
update their own profile.

## Regression tests
The new test file covers disallowed student and sponsor writes, permitted admin
updates, permitted reads, and sponsor self-service edits. The existing CRUD test
fixture is updated to represent an authenticated Auth0 admin instead of a
role-less Django user.

```sh
cd backend
python -m pytest -q user/tests/test_record_security.py user/tests/test_views.py
python -m pytest -q
```

## Limitations and follow-up
- These endpoints still expose roster **reads** to all authenticated users.
  Confirm which student/sponsor fields truly need to be public within the app.
- These tests bypass the live Auth0 provider via Django REST Framework's
  `force_authenticate`; perform a real sponsor/student/admin regression test
  before production rollout.
- Does not change emails, project assignment, attachment logic, or user-role
  creation in Auth0.
- Apply only after reviewing any new PRs that touch the `backend/user/` paths.
