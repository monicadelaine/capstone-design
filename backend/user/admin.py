from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from import_export.admin import ImportExportModelAdmin

from emails.utils import email_client
from project.models import Project, Attachment
from user.models import Sponsor, Student
from user.resources import SponsorResource, StudentResource


@admin.register(Sponsor)
class SponsorAdmin(ImportExportModelAdmin):
    resource_classes = [SponsorResource]
    list_display = ['name', 'email', 'projects', 'organization']
    list_display_links = ['name']
    list_filter = ['organization']
    search_fields = ['last_name', 'first_name', 'organization', 'email']
    ordering = ['last_name', 'first_name', 'organization', 'id']

    actions = ['export_sponsor_outreach_eml', 'send_sponsor_outreach_email',
               'export_project_presentation_eml', 'send_project_presentation_email']

    def send_sponsor_outreach_email(self, request, queryset):
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('admin:user_sponsor_changelist'))
        
        # Check if form was submitted (has semester field) vs just selecting action
        if request.method == 'POST' and request.POST.get('semester'):
            semester = request.POST.get('semester', 'spring')
            collection_date = request.POST.get('collection_date', 'TBD')
            from_email = request.POST.get('from_email')
            smtp_host = request.POST.get('smtp_host')
            smtp_port = request.POST.get('smtp_port')
            smtp_username = request.POST.get('smtp_username')
            smtp_password = request.POST.get('smtp_password')

            recipients = [s.email for s in queryset]

            try:
                kwargs = {}
                if from_email:
                    kwargs['from_email'] = from_email
                if smtp_host:
                    kwargs['smtp_host'] = smtp_host
                if smtp_port:
                    kwargs['smtp_port'] = smtp_port
                if smtp_username:
                    kwargs['smtp_username'] = smtp_username
                if smtp_password:
                    kwargs['smtp_password'] = smtp_password

                email_client.send_sponsor_outreach(
                    recipient_list=recipients,
                    semester=semester,
                    collection_date=collection_date,
                    **kwargs
                )
                self.message_user(request, f'Successfully sent outreach email to {len(recipients)} sponsor(s)')
            except Exception as e:
                self.message_user(request, f'Error sending email: {str(e)}', level='error')

            return HttpResponseRedirect(reverse('admin:user_sponsor_changelist'))

        # Show the form
        selected = queryset.values_list('id', flat=True)
        return render(
            request,
            'admin/sponsor_outreach_action.html',
            {
                'queryset': queryset,
                'title': 'Send Sponsor Outreach Email',
                'action_checkbox_name': ACTION_CHECKBOX_NAME,
                'selected_ids': list(selected),
            }
        )
    send_sponsor_outreach_email.short_description = 'Send Sponsor Outreach Email'

    def export_sponsor_outreach_eml(self, request, queryset):
        if request.method == 'POST':
            semester = request.POST.get('semester', 'spring')
            collection_date = request.POST.get('collection_date', 'TBD')

            if request.POST.get('create_btn'):
                html_content = email_client.render_sponsor_outreach_html(semester, collection_date)

                # Create EML for first sponsor (for the To field)
                first_sponsor = queryset.first()
                eml_content = email_client.convert_html_to_eml(
                    html_content,
                    subject=f"UA CS Capstone Project Opportunity - {semester.capitalize()}",
                    to_email=first_sponsor.email if first_sponsor else ''
                )

                attachment = Attachment.objects.create(
                    title=f"Sponsor Outreach Email - {semester.capitalize()} {collection_date}",
                    content=eml_content
                )

                download_url = f"/admin/project/attachment/{attachment.id}/download/"

                self.message_user(
                    request,
                    f'Exported EML file created: {attachment.title}. '
                    f'<a href="{download_url}" target="_blank">Download</a>',
                    level='info',
                    extra_tags='safe'
                )
                return HttpResponseRedirect(reverse('admin:user_sponsor_changelist'))

            if request.POST.get('preview_btn'):
                preview_html = email_client.render_sponsor_outreach_html(semester, collection_date)
                return render(
                    request,
                    'admin/export_sponsor_outreach.html',
                    {
                        'queryset': queryset,
                        'title': 'Export Sponsor Outreach as EML',
                        'action_checkbox_name': ACTION_CHECKBOX_NAME,
                        'semester': semester,
                        'collection_date': collection_date,
                        'preview_html': preview_html,
                    }
                )

        return render(
            request,
            'admin/export_sponsor_outreach.html',
            {
                'queryset': queryset,
                'title': 'Export Sponsor Outreach as EML',
                'action_checkbox_name': ACTION_CHECKBOX_NAME,
                'semester': 'spring',
                'collection_date': 'TBD',
            }
        )
    export_sponsor_outreach_eml.short_description = 'Export Sponsor Outreach as EML'

    def send_project_presentation_email(self, request, queryset):
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('admin:user_sponsor_changelist'))
        
        # Check if form was submitted (has date field) vs just selecting action
        if request.method == 'POST' and request.POST.get('date'):
            date = request.POST.get('date', 'TBD')
            time = request.POST.get('time', 'TBD')
            zoom_details = request.POST.get('zoom_details', 'TBD')
            from_email = request.POST.get('from_email')
            smtp_host = request.POST.get('smtp_host')
            smtp_port = request.POST.get('smtp_port')
            smtp_username = request.POST.get('smtp_username')
            smtp_password = request.POST.get('smtp_password')

            total_sent = 0
            for sponsor in queryset:
                projects = Project.objects.filter(sponsor=sponsor)
                if not projects:
                    continue

                kwargs = {}
                if from_email:
                    kwargs['from_email'] = from_email
                if smtp_host:
                    kwargs['smtp_host'] = smtp_host
                if smtp_port:
                    kwargs['smtp_port'] = smtp_port
                if smtp_username:
                    kwargs['smtp_username'] = smtp_username
                if smtp_password:
                    kwargs['smtp_password'] = smtp_password

                for project in projects:
                    try:
                        email_client.send_project_presentation_for_project(
                            recipient_list=[sponsor.email],
                            date=date,
                            time=time,
                            project=project,
                            zoom_details=zoom_details,
                            **kwargs
                        )
                        total_sent += 1
                    except Exception as e:
                        self.message_user(request, f'Error sending for {project.name}: {str(e)}', level='error')

            self.message_user(request, f'Successfully sent {total_sent} project presentation email(s)')
            return HttpResponseRedirect(reverse('admin:user_sponsor_changelist'))

        # Show the form
        first_sponsor = queryset.first()
        if first_sponsor:
            projects = Project.objects.filter(sponsor=first_sponsor)
            default_contact_name = f"{first_sponsor.first_name} {first_sponsor.last_name}"
            default_contact_email = first_sponsor.email
        else:
            projects = []
            default_contact_name = ''
            default_contact_email = ''

        return render(
            request,
            'admin/project_presentation_action.html',
            {
                'queryset': queryset,
                'title': 'Send Project Presentation Email',
                'action_checkbox_name': ACTION_CHECKBOX_NAME,
                'projects': projects,
                'contact_name': default_contact_name,
                'contact_email': default_contact_email,
            }
        )
    send_project_presentation_email.short_description = 'Send Project Presentation Email'

    def export_project_presentation_eml(self, request, queryset):
        if request.method == 'POST':
            date = request.POST.get('date', 'TBD')
            time = request.POST.get('time', 'TBD')
            zoom_details = request.POST.get('zoom_details', 'TBD')

            if request.POST.get('create_btn'):
                created_count = 0
                for sponsor in queryset:
                    projects = Project.objects.filter(sponsor=sponsor)
                    for project in projects:
                        html_content = email_client.render_project_presentation_single_html(
                            date=date,
                            time=time,
                            project=project,
                            zoom_details=zoom_details
                        )

                        eml_content = email_client.convert_html_to_eml(
                            html_content,
                            subject=f"Project Presentation: {project.name}",
                            to_email=sponsor.email
                        )
                        eml_attachment = Attachment.objects.create(
                            title=f"Project Presentation - {project.name}",
                            content=eml_content,
                            project=project
                        )
                        created_count += 1

                self.message_user(
                    request,
                    f'Created {created_count} EML file(s)',
                    level='info',
                )
                return HttpResponseRedirect(reverse('admin:user_sponsor_changelist'))

            if request.POST.get('preview_btn'):
                first_sponsor = queryset.first()
                projects = list(Project.objects.filter(sponsor=first_sponsor)) if first_sponsor else []
                preview_project = projects[0] if projects else None
                preview_html = ''
                if preview_project:
                    preview_html = email_client.render_project_presentation_single_html(
                        date=date,
                        time=time,
                        project=preview_project,
                        zoom_details=zoom_details
                    )

                return render(
                    request,
                    'admin/export_project_presentation.html',
                    {
                        'queryset': queryset,
                        'title': 'Export Project Presentation as EML',
                        'action_checkbox_name': ACTION_CHECKBOX_NAME,
                        'date': date,
                        'time': time,
                        'zoom_details': zoom_details,
                        'projects': projects,
                        'preview_html': preview_html,
                    }
                )

        first_sponsor = queryset.first()
        if first_sponsor:
            projects = list(Project.objects.filter(sponsor=first_sponsor))
            default_contact_name = f"{first_sponsor.first_name} {first_sponsor.last_name}"
            default_contact_email = first_sponsor.email
        else:
            projects = []
            default_contact_name = ''
            default_contact_email = ''

        return render(
            request,
            'admin/export_project_presentation.html',
            {
                'queryset': queryset,
                'title': 'Export Project Presentation as EML',
                'action_checkbox_name': ACTION_CHECKBOX_NAME,
                'date': 'TBD',
                'time': 'TBD',
                'zoom_details': '',
                'projects': projects,
                'contact_name': default_contact_name,
                'contact_email': default_contact_email,
            }
        )
    export_project_presentation_eml.short_description = 'Export Project Presentation as EML'

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            sponsor = self.get_object(request, object_id)
            attachments = Attachment.objects.filter(project__sponsor=sponsor).order_by('-created_at')[:10]
            extra_context['recent_attachments'] = attachments
        return super().changeform_view(request, object_id, form_url, extra_context)

    def projects(self, obj):
        url = (
            reverse('admin:project_project_changelist')
            + '?'
            + urlencode({'sponsor__id__exact': obj.id})
        )
        count = Project.objects.filter(sponsor=obj).count()
        return format_html(f'<a href="{url}">{count}</a>')


@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_classes = [StudentResource]
    readonly_fields = ['id']

    list_display = ['cwid', 'name', 'email', 'major_code', 'class_code']
    list_display_links = ['cwid', 'name']
    list_filter = ['major_code', 'class_code']
    search_fields = ['last_name', 'first_name', 'cwid', 'email']
    ordering = ['last_name', 'first_name', 'cwid']
