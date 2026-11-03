## Configuration

Configure emails via the environment variables in your `.env.dev` file as so:

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_BACKEND` | Email backend | `django.core.mail.backends.console.EmailBackend` |
| `EMAIL_HOST` | SMTP server hostname | `localhost` |
| `EMAIL_PORT` | SMTP server port | `1025` |
| `EMAIL_USE_TLS` | Use TLS | `False` |
| `EMAIL_HOST_USER` | SMTP username | (empty) |
| `EMAIL_HOST_PASSWORD` | SMTP password | (empty) |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@example.com` |
| `EMAIL_FAIL_SILENTLY` | Fail silently on error | `False` |
| `CAPSTONE_YEAR` | Year in the sponsor outreach subject | Current year |

### Production (Gmail SMTP)

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Note:** Gmail requires an App Password, not your regular password. Generate one at: https://myaccount.google.com/apppasswords. If you can't, enable two factor authentication on your account.


### Using the API

**Send custom email:**
```bash
POST /api/v1/emails/send
{
    "subject": "Hello",
    "message": "Body text",
    "recipients": ["email1@example.com", "email2@example.com"],
    "html_message": "<p>HTML</p>"
}
```

**Send sponsor outreach:**
```bash
POST /api/v1/emails/sponsor-outreach
{
    "recipients": "email1@example.com, email2@example.com",
    "semester": "spring",
    "collection_date": "Fall 2026 (8/24/26)"
}
```

**Send project presentation:**
```bash
POST /api/v1/emails/project-presentation
{
    "recipients": "email@example.com",
    "date": "Tuesday Sep 15, 2026",
    "time": "3:45 - 4:00",
    "project_name": "Project Name",
    "project_description": "Description of the project",
    "contact_name": "John Doe",
    "contact_email": "john@example.com",
    "zoom_details": "Zoom meeting link and details"
}
```

## Templates

Email templates are located in `backend/emails/templates/emails/`:

- `sponsor_outreach.html` - Sponsor outreach email
- `project_presentation.html` / `project_presentation_single.html` - Project presentation invitation email
- `base.html` - Base HTML template
- `assignment_posted.html` / `deadline_reminder.html` - Student notification emails

## Admin

The Vue app has no email pages. Admins send and export these emails from Django admin: select sponsors under Users > Sponsors and choose an email action.

## Student notifications

Two emails go to students (PBI-05, #54). Both are plain `EmailClient` sends, so in local development they land in Mailhog at http://localhost:8025.

| Email | When | Who | Template |
|-------|------|-----|----------|
| Assignment posted | When an admin approves a proposed assignment (Semester admin > Propose assignments > Approve) | Only students whose assignment is new or moved to a different project | `assignment_posted.html` |
| Ranking deadline reminder | Once per semester, when the ranking deadline (`Semester.assignment_date`) is within `DEADLINE_REMINDER_DAYS` days | Students with no preferences saved for that semester | `deadline_reminder.html` |

Approving still saves the assignments if the emails cannot be sent; the admin sees a warning instead.

The reminder is a management command. Run it daily (cron, Cloud Scheduler); it does nothing until a semester is due and never reminds the same semester twice (`Semester.reminder_sent_at`):

```bash
docker-compose -f docker-compose.dev.yml exec backend python manage.py send_deadline_reminders --dry-run   # list recipients, send nothing
docker-compose -f docker-compose.dev.yml exec backend python manage.py send_deadline_reminders             # send
docker-compose -f docker-compose.dev.yml exec backend python manage.py send_deadline_reminders --force     # resend to a semester already reminded
docker-compose -f docker-compose.dev.yml exec backend python manage.py send_deadline_reminders --days 5    # override DEADLINE_REMINDER_DAYS
```

The reminder goes to every student without preferences, because a student is not linked to a semester until they rank. Remove students from past semesters from the Student table (or check `--dry-run`) before the first reminder of a semester.

| Variable | Description | Default |
|----------|-------------|---------|
| `DEADLINE_REMINDER_DAYS` | Days before the deadline the reminder goes out | `3` |
| `APP_URL` | Base URL used for the links in the emails | `http://localhost:5173` |
| `ALLOW_STUDENT_EMAILS` | Student emails are refused unless the mail backend is a local catcher (console, Mailhog). Set `True` to send to real students | `False` |

## Configuration

Configure emails via the environment variables in your `.env.dev` file as so:

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_BACKEND` | Email backend | `django.core.mail.backends.console.EmailBackend` |
| `EMAIL_HOST` | SMTP server hostname | `localhost` |
| `EMAIL_PORT` | SMTP server port | `1025` |
| `EMAIL_USE_TLS` | Use TLS | `False` |
| `EMAIL_HOST_USER` | SMTP username | (empty) |
| `EMAIL_HOST_PASSWORD` | SMTP password | (empty) |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@example.com` |
| `EMAIL_FAIL_SILENTLY` | Fail silently on error | `False` |
| `CAPSTONE_YEAR` | Year in the sponsor outreach subject | Current year |

### Production (Gmail SMTP)

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Note:** Gmail requires an App Password, not your regular password. Generate one at: https://myaccount.google.com/apppasswords. If you can't, enable two factor authentication on your account.


### Using the API

**Send custom email:**
```bash
POST /api/v1/emails/send
{
    "subject": "Hello",
    "message": "Body text",
    "recipients": ["email1@example.com", "email2@example.com"],
    "html_message": "<p>HTML</p>"
}
```

**Send sponsor outreach:**
```bash
POST /api/v1/emails/sponsor-outreach
{
    "recipients": "email1@example.com, email2@example.com",
    "semester": "spring",
    "collection_date": "Fall 2026 (8/24/26)"
}
```

**Send project presentation:**
```bash
POST /api/v1/emails/project-presentation
{
    "recipients": "email@example.com",
    "date": "Tuesday Sep 15, 2026",
    "time": "3:45 - 4:00",
    "project_name": "Project Name",
    "project_description": "Description of the project",
    "contact_name": "John Doe",
    "contact_email": "john@example.com",
    "zoom_details": "Zoom meeting link and details"
}
```

## Templates

Email templates are located in `backend/emails/templates/emails/`:

- `sponsor_outreach.html` - Sponsor outreach email
- `project_presentation.html` / `project_presentation_single.html` - Project presentation invitation email
- `base.html` - Base HTML template

## Frontend

The frontend provides pages for sending emails:

1. **Send Email** (`/email`) - Send custom emails
2. **Sponsor Outreach** (`/sponsor-outreach`) - Send sponsor outreach template
3. **Project Presentation** (`/project-presentation`) - Send project presentation invitation

Access these at `http://localhost:5173/email`, `http://localhost:5173/sponsor-outreach`, and `http://localhost:5173/project-presentation` when the frontend is running.
