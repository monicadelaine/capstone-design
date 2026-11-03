from django.contrib import admin

from emails.models import EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Read-only record of sent emails (#73)."""

    list_display = ['sent_at', 'kind', 'subject', 'recipient_count', 'sent_by', 'success']
    list_filter = ['kind', 'success']
    search_fields = ['subject', 'sent_by']
    readonly_fields = ['sent_at', 'kind', 'subject', 'recipients', 'sent_by', 'success', 'error']

    @admin.display(description='Recipients')
    def recipient_count(self, obj):
        return len(obj.recipients)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
