# Backend via Django REST Framework and PostgreSQL

## Manipulating Objects

The REST API can be interacted with by using ```curl```, the [Django Browsable API](https://www.django-rest-framework.org/topics/browsable-api/), or any other software that can send REST requests via HTTP (including your code).

| Action | Request | Route |
| - | - | - |
| Create | PUT | ```/api/v1/projects/create/``` |
| Read | GET | ```/api/v1/projects/``` or ```/api/v1/projects/<id>``` |
| Update | PATCH/PUT | ```/api/v1/projects/<id>``` |
| Delete | DELETE | ```/api/v1/projects/<id>``` |

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
- **Admin action tests** (`project/tests/test_admin.py`)
    - Project admin actions:
        - Change project status
        - Assign selected projects to semester(s)
        - Remove selected projects from a semester
    - Preference admin action:
        - Assign selected students to a project with create/update/error-path coverage

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

#### `emails` app

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
- **Admin tests** (`emails/tests/test_admin.py`)
    - Custom admin-site URL registration
    - Sponsor outreach and project presentation admin views (GET render + POST send/redirect)

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

## Creating New Models (w/ associated tables)

The ```project``` subdirectory of the ```backend``` directory represents a standalone Python module, that is used by the ```core``` module. The ```Project``` module will hold and route models relating to non-user related objects, and the ```User``` module will hold user models and user-related models. Each model in ```models.py``` requires an entry in the associated ```serializers.py```, ```views.py```, and ```urls.py``` classes.

Use the Python files in the ```backend/project/``` directory to see the ```Project``` model as an example. Please follow the [Django Coding style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/#model-style).

1. RUN MIGRATIONS BEFORE MAKING EDITS TO THE CODEBASE (Your containers will need to be running to run this command):

    1. ```docker-compose -f <compose script> exec backend python manage.py migrate```

2. Define the model for your table in ```backend/<module>/models.py```
    > Django automatically creates and assigns primary key ID fields to every model, so you do not need to add your own ID fields

    > Project, Preference, and Assignment objects should go under the ```Project``` module, while Sponsors, Students, Admins, login info and other user related info should go under the ```User``` module

3. Add a class in ```backend/<module>/serializers.py```

4. Create a ```ViewSet``` for the new model in ```backend/<module>/views.py```

5. Register a route for the new model in ```backend/<module>/urls.py```

6. Spin up the containers and run migrations

    1. ```docker-compose -f <compose script> exec backend python manage.py makemigrations```

    2. ```docker-compose -f <compose script> exec backend python manage.py migrate```

7. Test CRUD operations at ```http://localhost:8000/api/v1/<your new object>/```
