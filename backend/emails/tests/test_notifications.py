from datetime import timedelta

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from emails import notifications
from emails.notifications import NotificationError, notify_assignments_posted, send_deadline_reminders
from project.models import Assignment, Preference, Project, Semester
from user.models import Sponsor, Student


@pytest.fixture
def semester(db):
    now = timezone.now()
    return Semester.objects.create(
        semester=Semester.get_semester_by_date(now), year=now.year,
        assignment_date=now + timedelta(days=2),
    )


@pytest.fixture
def project(db, semester):
    sponsor = Sponsor.objects.create(first_name='Ada', last_name='Lovelace', email='ada@example.com')
    project = Project.objects.create(name='Engine Tracker', sponsor=sponsor)
    semester.projects.add(project)
    return project


def make_student(n):
    return Student.objects.create(cwid=f'{20000000 + n}', first_name=f'First{n}', last_name=f'Last{n}',
                                  email=f'student{n}@crimson.ua.edu')


class TestSendingAllowed:
    def test_locmem_and_console_are_allowed(self, settings):
        for backend in ('locmem', 'console'):
            settings.EMAIL_BACKEND = f'django.core.mail.backends.{backend}.EmailBackend'
            assert notifications.sending_allowed()

    def test_smtp_to_mailhog_is_allowed(self, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = 'mailhog'
        assert notifications.sending_allowed()

    def test_smtp_to_a_real_host_is_refused(self, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = 'smtp.gmail.com'
        settings.ALLOW_STUDENT_EMAILS = False
        assert not notifications.sending_allowed()
        with pytest.raises(NotificationError, match='ALLOW_STUDENT_EMAILS'):
            notifications.require_sending_allowed()

    def test_real_host_needs_the_explicit_setting(self, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = 'smtp.gmail.com'
        settings.ALLOW_STUDENT_EMAILS = True
        assert notifications.sending_allowed()


@pytest.mark.django_db
class TestAssignmentPosted:
    def test_emails_only_the_listed_students(self, semester, project):
        notified, skipped = make_student(1), make_student(2)
        Assignment.objects.create(student=notified, semester=semester, project=project)
        Assignment.objects.create(student=skipped, semester=semester, project=project)

        assert notify_assignments_posted(semester, [notified.id]) == (1, 0)

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == ['student1@crimson.ua.edu']
        assert 'Engine Tracker' in message.body
        assert '/student/assignment' in message.body
        assert 'First1' in message.body

    def test_refuses_to_send_outside_a_mail_catcher(self, semester, project, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = 'smtp.gmail.com'
        settings.ALLOW_STUDENT_EMAILS = False
        student = make_student(1)
        Assignment.objects.create(student=student, semester=semester, project=project)
        with pytest.raises(NotificationError):
            notify_assignments_posted(semester, [student.id])
        assert mail.outbox == []

    def test_one_failure_does_not_stop_the_rest(self, semester, project, monkeypatch):
        for n in (1, 2):
            Assignment.objects.create(student=make_student(n), semester=semester, project=project)
        real_send = notifications.EmailClient.send_assignment_posted
        calls = []

        def flaky(self, student, assignment):
            calls.append(student.id)
            if len(calls) == 1:
                raise RuntimeError('smtp down')
            return real_send(self, student, assignment)

        monkeypatch.setattr(notifications.EmailClient, 'send_assignment_posted', flaky)
        sent, failed = notify_assignments_posted(semester, [s.id for s in Student.objects.all()])
        assert (sent, failed) == (1, 1)


@pytest.mark.django_db
class TestDeadlineReminders:
    def test_emails_students_who_have_not_ranked(self, semester, project):
        ranked, waiting = make_student(1), make_student(2)
        Preference.objects.create(student=ranked, project=project, rank=1)

        results = send_deadline_reminders()

        assert [(r[0], r[1], r[2], r[3]) for r in results] == [(semester, ['student2@crimson.ua.edu'], 1, 0)]
        assert [m.to for m in mail.outbox] == [['student2@crimson.ua.edu']]
        assert 'First2' in mail.outbox[0].body
        assert '/student/submit' in mail.outbox[0].body
        assert '2 days' in mail.outbox[0].body
        semester.refresh_from_db()
        assert semester.reminder_sent_at is not None

    def test_sends_once_per_semester(self, semester, project):
        make_student(1)
        send_deadline_reminders()
        assert send_deadline_reminders() == []
        assert len(mail.outbox) == 1

    def test_force_sends_again(self, semester, project):
        make_student(1)
        send_deadline_reminders()
        send_deadline_reminders(force=True)
        assert len(mail.outbox) == 2

    def test_too_early_is_not_due(self, semester, project, settings):
        make_student(1)
        assert send_deadline_reminders(days=1) == []
        assert mail.outbox == []

    def test_days_default_comes_from_settings(self, semester, project, settings):
        make_student(1)
        settings.DEADLINE_REMINDER_DAYS = 1
        assert send_deadline_reminders() == []
        settings.DEADLINE_REMINDER_DAYS = 2
        assert len(send_deadline_reminders()) == 1

    def test_passed_deadline_is_not_due(self, semester, project):
        make_student(1)
        Semester.objects.update(assignment_date=timezone.now() - timedelta(hours=1))
        assert send_deadline_reminders() == []
        assert mail.outbox == []

    def test_dry_run_sends_and_records_nothing(self, semester, project):
        make_student(1)
        results = send_deadline_reminders(dry_run=True)
        assert results[0][1] == ['student1@crimson.ua.edu']
        assert mail.outbox == []
        semester.refresh_from_db()
        assert semester.reminder_sent_at is None

    def test_a_run_where_every_send_fails_can_be_retried(self, semester, project, monkeypatch):
        make_student(1)

        def broken(self, student, semester, days_left):
            raise RuntimeError('smtp login failed')

        monkeypatch.setattr(notifications.EmailClient, 'send_deadline_reminder', broken)
        results = send_deadline_reminders()
        assert (results[0][2], results[0][3]) == (0, 1)
        semester.refresh_from_db()
        assert semester.reminder_sent_at is None

        monkeypatch.undo()
        assert send_deadline_reminders()[0][2] == 1
        assert len(mail.outbox) == 1

    def test_refuses_to_send_outside_a_mail_catcher(self, semester, project, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = 'smtp.gmail.com'
        settings.ALLOW_STUDENT_EMAILS = False
        make_student(1)
        with pytest.raises(NotificationError):
            send_deadline_reminders()
        semester.refresh_from_db()
        assert semester.reminder_sent_at is None

    def test_command_dry_run_lists_recipients(self, semester, project, capsys):
        make_student(1)
        call_command('send_deadline_reminders', '--dry-run')
        out = capsys.readouterr().out
        assert 'would email 1 student(s)' in out and 'student1@crimson.ua.edu' in out
        assert mail.outbox == []

    def test_command_sends(self, semester, project, capsys):
        make_student(1)
        call_command('send_deadline_reminders')
        assert 'emailed 1 student(s), 0 failed' in capsys.readouterr().out
        assert len(mail.outbox) == 1
