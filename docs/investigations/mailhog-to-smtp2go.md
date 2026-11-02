# Mailhog to SMTP2GO and Gmail: Real Delivery for Student Notification Emails (#54)

**Date:** 2026-11-02 · **Author:** Jayden White · **Related:** #54 (PBI-05), PR #86
**Question:** Mailhog proves our emails are built correctly, but it never delivers anything. How do we confirm a student notification reaches a real inbox, without risking mail to real students?
**Answer:** Keep Mailhog as the default for development and tests, and use SMTP2GO (`mail.smtp2go.com:587`, STARTTLS) only when verifying real delivery. The reminder reached the author's inbox through it. The dev config then moved to Gmail SMTP (`smtp.gmail.com:587`, App Password), and the reminder reached the inbox through that too.
**Status:** real delivery verified for development with both providers for the reminder. The assignment-posted email was accepted by SMTP2GO and by Gmail (`Failed: 0`); inbox receipt of that one is not confirmed. A team-owned sending account and domain for staging is still open (#45, #52).

## Why Mailhog was not enough

Mailhog is a local mail catcher: the dev stack points `EMAIL_HOST` at the `mailhog` container (port 1025, inbox at http://localhost:8025), so every message stays on the machine. That is the right default, and it is why the test suite and the first manual checks used it. It cannot show:

- that the provider accepts our sender address and credentials,
- that a message is delivered, or is filtered as spam,
- what a student actually sees in a mail client.

#54 asks for both emails to be visible in Mailhog, and its checklist says to avoid real bulk email while testing. So real delivery had to be possible but deliberate.

## What was built

| Part | Detail |
|---|---|
| Sending guard | `backend/emails/notifications.py` refuses to send student email unless the backend is a local catcher (console, locmem, file, dummy) or the SMTP host is `localhost` or `mailhog`. `ALLOW_STUDENT_EMAILS=True` lifts it. Default is `False`. |
| Test recipient | The author's own address was the only real address that could receive mail. For the reminder, three fake `@example.com` students had already ranked, so the command skipped them; `--dry-run` listed the recipients before anything was sent. For the assignment email, the fake students were deleted first (see "Problems found along the way"). |
| Settings | `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, set in the gitignored `.env.dev`. `.env.example` keeps the Mailhog values. |

## Process

The first provider attempt did not work, so the path was:

| Step | Host | Result | Cause |
|---|---|---|---|
| 1 | `mailhog:1025` | Works | Local only, nothing delivered |
| 2 | `mailgun` | DNS failure | Not a hostname; the SMTP server is `smtp.mailgun.org` |
| 3 | `smtp.mailgun.org` 587, 2525, 465 | Connected, TLS fine, server closed the connection at `AUTH` | Username was a university address, not a login on the Mailgun domain; the password length matched a different service's. A Mailgun sandbox domain also refuses anyone not on its authorized-recipient list |
| 4 | `smtp.smtp2go.org` | DNS failure | Wrong domain; the host does not exist |
| 5 | `mail.smtp2go.com` 587 | Works | Login accepted on 587 and 2525 (checked with a login-only probe, nothing sent) |
| 6 | `smtp.gmail.com` 587 | Works | `.env.dev` switched to the README's Gmail settings. Reminder: `emailed 1 student(s), 0 failed`, and the message arrived |

Gmail with an App Password (the "Production (Gmail SMTP)" path in `backend/emails/README.md`) and a UA Microsoft 365 account (SMTP AUTH is often disabled for student accounts) were considered and not used at that point. Gmail was adopted afterwards (step 6). The reason SMTP2GO was picked over fixing the Mailgun credentials is not recorded here.

Result on step 5: `Fall 2026: emailed 1 student(s), 0 failed. sent to <author address>`, and the message arrived. The assignment-posted email, sent through the real approve view, reported `Emailed 1 student(s) their assignment. Failed: 0`.

## Move to Gmail SMTP

After the SMTP2GO test, the mail section of the gitignored `.env.dev` was rewritten with the Gmail settings documented in `backend/emails/README.md`:

| Setting | SMTP2GO (before) | Gmail (now) |
|---|---|---|
| `EMAIL_HOST` | `mail.smtp2go.com` | `smtp.gmail.com` |
| Port and TLS | 587, STARTTLS | 587, STARTTLS (unchanged) |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP user created in the SMTP2GO dashboard | A Gmail address named for the course (not the author's personal address) and a 16-character Google App Password |
| `DEFAULT_FROM_EMAIL` | An address verified in SMTP2GO | The same Gmail address as the login, since Gmail sends as the authenticated account |

Only the mail lines changed; every other setting in the file is untouched, and the `MAIL_FAIL_SILENTLY` typo became `EMAIL_FAIL_SILENTLY`, the name Django reads. The working SMTP2GO login was saved to a backup outside the repository before it was overwritten, so the move can be reversed.

Gmail refuses a normal account password for SMTP: it needs 2-step verification on the account and an App Password from https://myaccount.google.com/apppasswords. The reason for moving from SMTP2GO to Gmail is not recorded here. The sending guard does not change: with `smtp.gmail.com` as host it blocks student email unless `ALLOW_STUDENT_EMAILS=True`.

### Gmail test

Checks before sending (values were not printed): the sender equals the login, the App Password is 16 characters, Compose parses `.env.dev`, and the backend started with the new values.

| Step | What ran | Result |
|---|---|---|
| Setup | Fall 2026 semester with a deadline two days out, one demo sponsor, two projects, the author's student record (no rankings), three fake students who had already ranked | 4 students, only the author eligible for a reminder |
| Dry run | `send_deadline_reminders --dry-run` | Listed only the author's address |
| Reminder | `send_deadline_reminders` | `emailed 1 student(s), 0 failed. sent to <author address>`; semester recorded as reminded; the message arrived |
| Form | The author logged in through Auth0 on the team tenant and submitted rankings in the real ranking form | 15 rankings saved, 5 High, 5 Medium, 5 Low |
| Approval | Propose and approve through the Semester admin's approve view, after checking the proposal held only the author | `Created: 1`, `Emailed 1 student(s) their assignment. Failed: 0`; assignment saved. Inbox receipt not confirmed |

The sample data and the test semester were deleted afterwards.

## Problems found along the way

| Problem | Effect | Fix |
|---|---|---|
| A run where every send failed still marked the semester as reminded | A failed run could not be retried without `--force` | The semester is recorded only if something was sent (or nobody needed a reminder); test added |
| Tests assumed `ALLOW_STUDENT_EMAILS` defaults to `False` | Three tests failed once `.env.dev` set it to `True` | Tests set it explicitly |
| Stray line and a merged line in `.env.dev` (`DEADLINE_REMINDER_DAYS=3PP_URL=...`) | Compose refused to read the file; backend crashed on `int('3PP_URL=...')` | Lines repaired by hand |
| An editor backup copy of the env file (`.~env.dev`) was staged by `git add -A` | Would have committed dev passwords | Caught by a diff scan before the commit; file moved out of the repo |
| The sample semester had only 2 projects, and the ranking form needs exactly 5 High, 5 Medium and 5 Low | The submit button stayed disabled, so the form could not be tested | Added 13 demo projects so the semester had 15 |
| The three fake students had ranked, so they were part of the proposal | Approving over real SMTP would have emailed `demo.*@example.com` for real, because the approve step emails every student whose assignment changed | Deleted the fake students and their rankings first; the script asserted the proposal held only the author before approving |

## Risks

- **Sender filtering.** Sending as a `@crimson.ua.edu` address through a third party, to a `crimson.ua.edu` inbox, can be junked or quarantined as spoofing. Check spam first if a message is missing.
- **Verified senders.** SMTP2GO sends only from addresses or domains verified in its dashboard. A personal sender address does not prove the course's own domain.
- **Gmail specifics.** The App Password grants mail access to that Google account, so it should be revoked if it leaks. The account used is named for the course, but who owns and controls it should be recorded. A Gmail account also has a daily sending cap (about 500 messages for a free account; verify before relying on it), which a cohort fits under but a mistaken `--force` rerun could eat into.
- **Credentials.** The SMTP username and password (SMTP2GO or Gmail) live in `.env.dev` only. They belong to one person's account, not the team's. They must never reach git; `.env.dev` and its variants are ignored, but editor backups are not.
- **Recipients.** The reminder goes to every student with no rankings, including students from past semesters still in the Student table. Run `--dry-run` first.
- **Approval emails the whole proposal.** Approving sends one real email to every student whose assignment is new or changed. There is no recipient allowlist, so any sample student with a ranking and a fake address gets real mail. The only protection is testing with a single real student.
- **Plan limits.** Free-tier sending limits were not checked. A full cohort is a few dozen to a few hundred messages per semester.

## Recommendation

1. Keep Mailhog as the default in `.env.example` and for tests. Use SMTP2GO or Gmail only to verify delivery, with one test student.
2. A course-named Gmail address with an App Password is fine for development and the demo. Before staging (#52), decide who owns the sending account (a team-owned SMTP2GO account with a verified domain, or a shared mailbox the instructor can access), and move the credentials there (#45 covers the matching Auth0 move). Do not use anyone's personal mailbox.
3. Leave `ALLOW_STUDENT_EMAILS=False` everywhere except a deliberate real send, and `--dry-run` before the first reminder of a semester.
4. Confirm inbox receipt of the assignment-posted email, which is still unchecked (the reminder is confirmed through both providers).
5. When testing the approve flow over real SMTP, use one real student and delete every other sample student first; consider adding a recipient allowlist for test sends so this does not depend on remembering.
6. Seed at least 15 projects in the test semester, otherwise the ranking form cannot be submitted.

Claude Code was used for formatting and proofreading this document.
