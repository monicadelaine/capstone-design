# Data Model

**Audience:** developers. Describes the database as it exists today (inherited from v1) and the changes we have decided to make.

Source of truth is `backend/user/models.py` and `backend/project/models.py`. Regenerate the diagram when those change.

## Current schema (v1, as of 2026-09-22)

```mermaid
erDiagram
    Sponsor ||--o{ Project : proposes
    Sponsor ||--o{ Feedback : writes
    Project ||--o{ Attachment : has
    Project ||--o{ Preference : ranked_in
    Project ||--o{ Assignment : staffed_by
    Project ||--o{ Feedback : about
    Project }o--o{ Semester : offered_in
    Semester ||--o{ Preference : during
    Semester ||--o{ Assignment : during
    Semester ||--o{ Feedback : during
    Student ||--o{ Preference : submits
    Student ||--o{ Assignment : receives

    Sponsor {
        int id PK
        string first_name
        string last_name
        string email
        string organization
        string phone_number
        int projects_allowed "default 3"
    }
    Student {
        int id PK
        string cwid UK "8 digits"
        string first_name
        string middle_name
        string last_name
        string preferred_name
        string email
        text description "skills, from ranking form"
        string class_code "FR SO JR SR GR"
        string major_code
    }
    Project {
        int id PK
        string name
        text description
        int sponsor FK
        text sponsor_availability
        string status "PNDG IP CMPL CNCL"
        string website
    }
    Semester {
        int id PK
        string semester "Fall Spring Summer"
        int year
        datetime assignment_date "ranking deadline"
    }
    Preference {
        string id PK "student-project slug"
        int student FK
        int project FK
        int rank "1 2 3"
        int semester FK
    }
    Assignment {
        string id PK "student-semester slug"
        int semester FK
        int student FK
        int project FK
    }
    Attachment {
        int id PK
        int project FK "nullable"
        file file
        string link
        string title
        text content "exported email"
    }
    Feedback {
        int id PK
        int sponsor FK
        int project FK
        int semester FK
        text text
    }
```

Constraints that exist: `Project(name, sponsor)` unique; `Semester(semester, year)` unique; `Student.cwid` unique; `Assignment` primary key is student plus semester, so one assignment per student per semester.

## What is wrong with it

From [docs/investigations/v1-reference.md](../investigations/v1-reference.md):

- No user record and no role column. Identity comes only from the Auth0 token; a student and a sponsor are rows in two unrelated tables keyed by a non-unique email.
- `Project.status` is set by hand and never derived from whether the project was assigned.
- No team concept and no per-project capacity. "Team" is implicitly every student assigned to the same project.
- `Preference` has no database uniqueness on (student, project, semester); it relies on the slug primary key.
- The ranking deadline (`Semester.assignment_date`) is enforced only in the browser.
- `Semester.year` maximum is computed at import time.

## Planned changes (Iteration 1 and 2)

| Change | Why | Where |
|---|---|---|
| Add `AppUser(email unique, role, is_active, created_at)` linked one-to-one to `Student` or `Sponsor` | Server-side role per [ADR-002](../decisions/ADR-002-auth.md) | new table |
| Make `Sponsor.email` and `Student.email` unique | One account per person | constraint |
| Add `Project.capacity` (int, default 4) | Team size limit the admin can set | column |
| Add `Team` (project, semester) with `Assignment.team` FK, or derive team = assignments grouped by project and semester | Depends on the sponsor's answer on team-preference input; decide after the sponsor meeting | pending |
| Unique constraint on `Preference(student, project, semester)` | Prevent duplicates at the database, not the client | constraint |
| Server-side check: reject preference writes after `Semester.assignment_date` | Deadline correctness | view |
| Derive `Project.status` from assignment state; keep a manual override for Cancelled | Remove a manual admin step | model method |
| Unique `Project(name)` per semester | Prior team's open bug #34 | constraint |
| `assigned_by`, `assigned_at` on `Assignment` | Audit trail if more than one admin | columns |

Anything requiring a migration goes through a pull request with a test.

## Scale assumptions

Under 100 users per semester, one traffic spike when rankings are due. No scaling work. Correctness is enforced by database constraints and the server-side deadline check, not by application-level locking.
