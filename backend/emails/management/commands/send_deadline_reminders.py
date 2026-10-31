from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from emails.notifications import NotificationError, send_deadline_reminders


class Command(BaseCommand):
    help = (
        'Email students who have not ranked projects when the ranking deadline is within '
        'DEADLINE_REMINDER_DAYS days. Each semester is reminded once. Run it daily from cron.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=None,
                            help=f'Days before the deadline (default {settings.DEADLINE_REMINDER_DAYS}).')
        parser.add_argument('--dry-run', action='store_true',
                            help='List who would be emailed. Sends nothing and records nothing.')
        parser.add_argument('--force', action='store_true',
                            help='Also remind semesters that were already reminded.')

    def handle(self, *args, **options):
        try:
            results = send_deadline_reminders(days=options['days'], dry_run=options['dry_run'], force=options['force'])
        except NotificationError as e:
            raise CommandError(str(e))
        if not results:
            self.stdout.write('No semester is due for a reminder.')
        for semester, emails, sent, failed in results:
            if options['dry_run']:
                self.stdout.write(f'{semester}: would email {len(emails)} student(s)')
                for email in emails:
                    self.stdout.write(f'  {email}')
            else:
                self.stdout.write(self.style.SUCCESS(f'{semester}: emailed {sent} student(s), {failed} failed.'))
                if not failed:
                    for email in emails:
                        self.stdout.write(f'  sent to {email}')
