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

## Admin

The Vue app has no email pages. Admins send and export these emails from Django admin: select sponsors under Users > Sponsors and choose an email action.

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
