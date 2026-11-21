# Backend via Django REST Framework and PostgreSQL

## Manipulating Objects

The REST API can be interacted with by using ```curl```, the [Django Browsable API](https://www.django-rest-framework.org/topics/browsable-api/), or any other software that can send REST requests via HTTP (including your code).

| Action | Request | Route |
| - | - | - |
| Create | POST | ```/api/v1/projects/``` |
| Read | GET | ```/api/v1/projects/``` or ```/api/v1/projects/<id>``` |
| Update | PATCH/PUT | ```/api/v1/projects/<id>``` |
| Delete | DELETE | ```/api/v1/projects/<id>``` |

### Who can write projects

Any authenticated user can read projects. Creating, editing, or deleting a project requires the `sponsor` or `admin` role from the Auth0 token. A sponsor can only act on projects under their own sponsor record (matched by email), cannot submit more than their `projects_allowed` count, and cannot reuse a project name. Admins bypass all three rules. See `project/permissions.py` and `ProjectSerializer` in `project/serializers.py`.

### Reviewing submitted projects

A sponsor's project starts as Pending and on no semester, so students do not see it. Only admins review. A project's `status` is read-only in the project API, so sponsors and students cannot change it by editing.

| Action | Request | Route |
| - | - | - |
| List projects waiting for review | GET | ```/api/v1/projects/pending/``` |
| Approve | POST | ```/api/v1/projects/<id>/approve/``` with optional `{"semester": <id>}`; the current semester by default |
| Reject | POST | ```/api/v1/projects/<id>/reject/``` |

Approving adds the project to the semester, which puts it in the students' project list. Rejecting marks it Cancelled and removes it from every semester; it is then visible only to admins and its own sponsor (in the project list and detail, `/sponsors/<id>/projects/`, and its attachments; see `hide_rejected_projects` in `project/permissions.py`), and it cannot be rejected once students are assigned to it. The same two actions are in Django admin under Projects ("Approve for a semester", "Reject"), with a "Waiting for review" filter. Logic: `project/review.py`.

## Admin Panel - Email Actions

The Django admin panel provides email functionality for sponsors. Access it at `/admin/`.

### Sponsor Actions

Navigate to **User → Sponsors**, select one or more sponsors, and choose an action from the dropdown:

| Action | Description |
| - | - |
| **Send Sponsor Outreach Email** | Sends an outreach email to selected sponsors via SMTP |
| **Export Sponsor Outreach as EML** | Creates an EML file that opens in your default email client |
| **Send Project Presentation Email** | Sends project presentation emails (one per project) to sponsors |
| **Export Project Presentation as EML** | Creates EML files for each project, ready to send from your email client |

### How to Use EML Files

When native SMTP sending doesn't work with the user's email address, use EML exports:

1. **Export** - Download the `.eml` file from Admin → Project → Attachments
2. **Open** - Double-click the `.eml` file to open in your default email client (Outlook, Mail.app, etc.)
3. **Send** - The email opens as a new unsent message with:
   - **To:** field pre-filled with sponsor's email
   - **From:** field uses your default email account
4. **Send** - Click send from your email client

### EML vs HTML Export

- **EML files**: Open directly in your email client as a ready-to-send email
- **HTML files**: Can be opened in a browser, then copy/paste into an email

## Unit Tests (Pytest)

The backend test suite uses `pytest` with `pytest-django` and is organized by app under each app's `tests/` directory.

### Test Stack and Conventions

- Test runner: `pytest`
- Django integration: `pytest-django` (`DJANGO_SETTINGS_MODULE = core.settings` in `pytest.ini`)
- API tests: DRF `APIClient`
- Common style:
    - Fixtures create reusable model data (`sample_sponsor`, `sample_student`, `sample_project`, etc.)
    - API tests use an authenticated client fixture (`force_authenticate`) for protected endpoints
    - External side effects (email sending, SMTP, template rendering) are mocked with `monkeypatch`
    - Tests are grouped in classes by responsibility (`Test...Model`, `Test...Serializer`, `Test...View`, `Test...Admin`)

### Current Test Coverage by App

#### `project` app

- **Model tests** (`project/tests/test_models.py`)
    - Validation and constraints for `Project`, `Semester`, `Preference`, `Assignment`, `Feedback`, and `Attachment`
    - ID/slug generation logic for `Preference` and `Assignment`
    - Attachment behavior for file/link/content validation and delete cleanup
- **Serializer tests** (`project/tests/test_serializers.py`)
    - Serialization and creation behavior for project/semester/preference/assignment/feedback/attachment serializers
    - Attachment serializer output behavior (including download URL expectations)
- **View tests** (`project/tests/test_views.py`)
    - CRUD and list/detail flows for projects, preferences, assignments, and feedback
    - Query/filter and error-path behavior
- **Project review tests** (`project/tests/test_review.py`)
    - Service: pending list, approve into the current or a chosen semester, reject, restoring a rejected project, refusing to reject a project with students assigned
    - API: pending list for admins, approve makes a project appear in the student list, reject hides it (list and detail), 400s for bad input, 403 for sponsors and students, status cannot be changed by editing
    - Project admin: approve and reject actions, the approve form, the "Waiting for review" filter
- **Admin action tests** (`project/tests/test_admin.py`)
    - Project admin actions:
        - Change project status
        - Assign selected projects to semester(s)
        - Remove selected projects from a semester
    - Preference admin action:
        - Assign selected students to a project with create/update/error-path coverage
- **Proposed-assignment tests** (`project/tests/test_assignment.py`)
    - CP-SAT model: known optimum, unused projects, exact and minimum team sizes, infeasible input
    - `propose`: cohort from the semester's preferences, cancelled projects skipped, clear errors; saves nothing
    - `approve`: creates or replaces `Assignment` rows; rejects tampered, expired, or stale proposals
    - Fairness and comparison (#107): a limit on the worst placement changes the result when it can be met and gets as close as possible when it cannot; the proposal reports the worst placement; team-size input is parsed and bad input explained; a comparison gives one column per setting, reports an infeasible one in its column, and saves nothing; opening a column gives a normal proposal and needs assignment permissions
    - Team sizes (#68): the semester's team size and minimum, a project's own maximum (smaller, larger, or below the minimum), seats counted per project, infeasible settings reported as a message, and moves and approval held to a project's own maximum
    - `edit` (moving students before approval): ranks recomputed, team-size violations listed, moves build on the last check, unknown students and off-semester projects rejected; approve saves the edited proposal and refuses one outside the size limits
    - Semester admin flow: propose action renders the table, moving a student re-checks it and approve saves the edit, violations disable Approve, unchecked moves are re-checked instead of saved, approve checks permissions

- **Endpoint permission tests** (`project/tests/test_endpoint_permissions_security.py`)
    - Attachments and feedback: only the owning sponsor or an admin may write, rejected projects stay hidden in lists and downloads
- **Demo data test** (`project/tests/test_seed_demo.py`)
    - `seed_demo` can be run twice without creating duplicates

#### `user` app

- **Model tests** (`user/tests/test_models.py`)
    - Sponsor and student creation, optional field defaults, and string/name helpers
    - Phone and CWID validation constraints
- **Serializer tests** (`user/tests/test_serializers.py`)
    - Serialization and creation for sponsor/student serializers
    - Invalid phone/CWID and duplicate CWID rejection paths
- **View tests** (`user/tests/test_views.py`)
    - Authenticated CRUD tests for sponsor and student endpoints
    - Validation-path tests (invalid phone, invalid/duplicate CWID)
- **Admin action tests** (`user/tests/test_admin.py`)
    - Sponsor admin actions:
        - Send sponsor outreach email
        - Export sponsor outreach as EML
        - Send project presentation emails
        - Export project presentation as EML
    - Includes render/preview branches and attachment creation assertions

- **Roster import tests** (`user/tests/test_resources.py`)
    - Blackboard CSV import: matching on CWID, re-import, bad rows reported with row numbers, header variants, email normalization, file encoding, who may import
- **Token validation tests** (`user/tests/test_authentication_security.py`)
    - RS256 only, a key ID is required, generic errors, signing-key cache and refresh
- **Record security tests** (`user/tests/test_record_security.py`)
    - Only admins write student and sponsor records; a sponsor can still edit their own profile; a student token cannot add itself to the roster

#### `emails` app

- **Notification tests** (`emails/tests/test_notifications.py`)
    - Assignment-posted and deadline-reminder emails: who receives them, the sending guard, the once-per-semester record

- **Serializer tests** (`emails/tests/test_serializers.py`)
    - Email serializer validation for recipients, required fields, and optional HTML body
- **View tests** (`emails/tests/test_views.py`)
    - `send_email`, `send_sponsor_outreach`, and `send_project_presentation` endpoint behavior
    - Success, validation failure, and exception handling branches
- **Utility tests** (`emails/tests/test_utils.py`)
    - `EmailClient` send paths (default send_mail and custom SMTP)
    - Templated email rendering helpers
    - Export conversion helpers (`convert_html_to_mhtml`, `convert_html_to_eml`)
    - Single-project presentation helper methods used by admin workflows
    - Outreach subject year from `CAPSTONE_YEAR` or an explicit `year`

### Running Tests

From the repository root with containers running:

1. Run all backend tests:

     `docker compose -f docker-compose.dev.yml exec backend pytest`

2. Run one app's tests:

     `docker compose -f docker-compose.dev.yml exec backend pytest project/tests -q`

     `docker compose -f docker-compose.dev.yml exec backend pytest user/tests -q`

     `docker compose -f docker-compose.dev.yml exec backend pytest emails/tests -q`

3. Run focused suites (examples):

     `docker compose -f docker-compose.dev.yml exec backend pytest project/tests/test_admin.py -q`

     `docker compose -f docker-compose.dev.yml exec backend pytest emails/tests/test_utils.py -q`

### Notes for Contributors

- Prefer adding tests in the same app that owns the behavior.
- Keep assertions focused on observable behavior (HTTP status/body, DB side effects, messages, and created attachments).
- Mock outbound integrations (email/SMTP) so tests remain deterministic and do not depend on network access.
- If a feature has model + serializer + view + admin behavior, add tests at each layer where business logic exists.

## Adding a model, an endpoint, or a screen

See [Adding a feature](../docs/development-guide/adding-a-feature.md) in the development guide: a worked example of a model field with its migration, an endpoint with its permission, a screen, and tests for each. The patterns the code follows are in [Conventions](../docs/development-guide/conventions.md).
