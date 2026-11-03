from django.db import models


class EmailLog(models.Model):
    """One row per email the app tried to send: when, what, to whom, and whether it went out.
    The body is not stored."""

    class Kind(models.TextChoices):
        CUSTOM = 'custom', 'Custom'
        SPONSOR_OUTREACH = 'sponsor_outreach', 'Sponsor outreach'
        PROJECT_PRESENTATION = 'project_presentation', 'Project presentation invite'
        ASSIGNMENT_POSTED = 'assignment_posted', 'Assignment posted'
        DEADLINE_REMINDER = 'deadline_reminder', 'Deadline reminder'

    sent_at = models.DateTimeField(auto_now_add=True)
    """[Default] When the send was attempted"""

    kind = models.CharField(max_length=30, choices=Kind.choices, default=Kind.CUSTOM)
    """[Required] Which email this was"""

    subject = models.TextField()
    """[Required] The subject line"""

    recipients = models.JSONField(default=list)
    """[Required] The recipient email addresses"""

    sent_by = models.CharField(max_length=254, blank=True)
    """[Optional] The admin who triggered the send, or 'system' for automatic emails"""

    success = models.BooleanField(default=True)
    """[Required] False if the mail backend raised an error"""

    error = models.TextField(blank=True)
    """[Optional] The error message when success is False"""

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.get_kind_display()} to {len(self.recipients)} recipient(s) at {self.sent_at:%Y-%m-%d %H:%M}'
