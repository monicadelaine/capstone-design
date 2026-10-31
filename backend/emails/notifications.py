"""Student notification emails (PBI-05, #54): assignment posted and ranking-deadline reminder.

Both are sent through EmailClient. Student emails only go out through a local mail catcher
(console, Mailhog) unless settings.ALLOW_STUDENT_EMAILS is True, so testing never mails real students.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from emails.utils import EmailClient
from project.models import Assignment, Preference, Semester
from user.models import Student

logger = logging.getLogger(__name__)

LOCAL_BACKENDS = {
    'django.core.mail.backends.console.EmailBackend',
    'django.core.mail.backends.locmem.EmailBackend',
    'django.core.mail.backends.filebased.EmailBackend',
    'django.core.mail.backends.dummy.EmailBackend',
}
LOCAL_SMTP_HOSTS = {'localhost', '127.0.0.1', '::1', 'mailhog'}


class NotificationError(Exception):
    """Emails were not sent. The message is shown to the admin."""


def sending_allowed():
    """True when mail goes to a local mail catcher, or real sending was switched on explicitly."""
    if settings.ALLOW_STUDENT_EMAILS or settings.EMAIL_BACKEND in LOCAL_BACKENDS:
        return True
    return (settings.EMAIL_BACKEND.endswith('smtp.EmailBackend')
            and settings.EMAIL_HOST in LOCAL_SMTP_HOSTS)


def require_sending_allowed():
    if not sending_allowed():
        raise NotificationError(
            f'EMAIL_BACKEND {settings.EMAIL_BACKEND} / host {settings.EMAIL_HOST} is not a local mail catcher. '
            'Set ALLOW_STUDENT_EMAILS=True to email real students.'
        )


def notify_assignments_posted(semester, student_ids):
    """Email each student in student_ids their assignment for the semester. Returns (sent, failed)."""
    require_sending_allowed()
    client = EmailClient()
    sent = failed = 0
    assignments = (Assignment.objects.filter(semester=semester, student_id__in=student_ids)
                   .select_related('student', 'project', 'semester'))
    for assignment in assignments:
        try:
            client.send_assignment_posted(assignment.student, assignment)
            sent += 1
        except Exception:
            logger.exception('Could not email assignment to student %s', assignment.student_id)
            failed += 1
    return sent, failed


def reminder_recipients(semester):
    """Students who have not ranked any project for the semester."""
    ranked = Preference.objects.filter(semester=semester).values('student_id')
    return Student.objects.exclude(id__in=ranked).exclude(email='').order_by('last_name', 'first_name')


def due_semesters(now=None, days=None):
    """Semesters whose deadline is within `days` days, not yet passed, and not yet reminded."""
    now = now or timezone.now()
    days = settings.DEADLINE_REMINDER_DAYS if days is None else days
    return Semester.objects.filter(
        reminder_sent_at__isnull=True,
        assignment_date__gt=now,
        assignment_date__lte=now + timedelta(days=days),
    )


def send_deadline_reminders(now=None, days=None, dry_run=False, force=False):
    """Send the ranking reminder for every semester that is due. Returns a list of
    (semester, [recipient emails], sent, failed). With dry_run, nothing is sent or recorded.
    With force, semesters already reminded are included."""
    now = now or timezone.now()
    semesters = due_semesters(now, days)
    if force:
        days = settings.DEADLINE_REMINDER_DAYS if days is None else days
        semesters = Semester.objects.filter(
            assignment_date__gt=now, assignment_date__lte=now + timedelta(days=days))
    if not dry_run and semesters.exists():
        require_sending_allowed()

    client = EmailClient()
    results = []
    for semester in semesters:
        recipients = list(reminder_recipients(semester))
        sent = failed = 0
        if not dry_run:
            days_left = max(round((semester.assignment_date - now).total_seconds() / 86400), 1)
            for student in recipients:
                try:
                    client.send_deadline_reminder(student, semester, days_left)
                    sent += 1
                except Exception:
                    logger.exception('Could not email reminder to student %s', student.id)
                    failed += 1
            # Only record the reminder when something went out (or nobody needed one), so a run
            # where every send failed, for example bad SMTP credentials, can simply be retried.
            if sent or not failed:
                semester.reminder_sent_at = now
                semester.save(update_fields=['reminder_sent_at'])
        results.append((semester, [s.email for s in recipients], sent, failed))
    return results
