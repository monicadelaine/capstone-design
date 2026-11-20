# SECURITY-02 — Attachment and feedback authorization (#57)

## Problem
Both endpoints previously permitted all logged-in users to perform writes. The
attachment download endpoint also fetched records directly, bypassing the
rejected-project visibility filter added under #67.

## Changes
- Authenticated users retain read access to attachments of visible projects.
- Only an administrator or the owning sponsor can create/change/delete project
  attachments. Sponsorship is checked against the authenticated account and
  against both the existing object and the destination project in the request.
- Unassigned attachments (which may be used for email exports) can be written
  through this API only by administrators.
- Direct attachment downloads use `hide_rejected_projects`, matching list and
  detail visibility; response download headers and file handling are unchanged.
- Only administrators or the associated sponsor can access feedback. Sponsor
  list/detail queries filter by sponsor and project ownership, and serializer
  validation prevents spoofing or changing either relationship.
- Existing records with mismatched feedback sponsor/project ownership are
  accessible to admins but not sponsors; review legacy data if needed.

## Verification

Run from `backend/` with the normal local test environment configured:

```sh
python -m pytest -v project/tests/test_endpoint_permissions_security.py
python -m pytest -q
```

Run the frontend tests and review the PR diff and CI before merging.

## Follow-up
Access to all student/sponsor roster fields and server-side assignment of Auth0
roles remain separate security tasks. Project-specific attachment confidentiality
may need a stricter read policy if the sponsor requires it.
