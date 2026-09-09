from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path


class EmailAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-sponsor-outreach/', self.admin_view(self.send_sponsor_outreach_view), name='send_sponsor_outreach'),
            path('send-project-presentation/', self.admin_view(self.send_project_presentation_view),
                 name='send_project_presentation'),
        ]
        return custom_urls + urls

    def send_sponsor_outreach_view(self, request):
        from django.contrib import messages
        from emails.utils import email_client

        emails_param = request.GET.get('emails', '')
        emails = [e.strip() for e in emails_param.split(',') if e.strip()]

        if request.method == 'POST':
            semester = request.POST.get('semester', 'Spring')
            collection_date = request.POST.get('collection_date', '')

            try:
                email_client.send_sponsor_outreach(
                    recipient_list=emails,
                    semester=semester,
                    collection_date=collection_date
                )
                messages.success(request, f'Successfully sent outreach email to {len(emails)} sponsor(s).')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')

            return HttpResponseRedirect('/admin/user/sponsor/')

        return render(request, 'email_form.html', {
            'title': 'Send Sponsor Outreach Email',
            'emails': ', '.join(emails),
            'action': 'sponsor_outreach',
            'semesters': ['Spring', 'Fall'],
            'semester_placeholder': 'Spring 2025 (1/14/25)',
        })

    def send_project_presentation_view(self, request):
        from django.contrib import messages
        from emails.utils import email_client

        emails_param = request.GET.get('emails', '')
        emails = [e.strip() for e in emails_param.split(',') if e.strip()]

        if request.method == 'POST':
            date = request.POST.get('date', 'TBD')
            time = request.POST.get('time', 'TBD')
            project_name = request.POST.get('project_name', 'TBD')
            project_description = request.POST.get('project_description', 'TBD')
            contact_name = request.POST.get('contact_name', 'TBD')
            contact_email = request.POST.get('contact_email', 'TBD')
            zoom_details = request.POST.get('zoom_details', 'TBD')

            try:
                for email in emails:
                    email_client.send_project_presentation(
                        recipient_list=[email],
                        date=date,
                        time=time,
                        project_name=project_name,
                        project_description=project_description,
                        contact_name=contact_name,
                        contact_email=contact_email,
                        zoom_details=zoom_details
                    )
                messages.success(request, f'Successfully sent presentation email to {len(emails)} sponsor(s).')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')

            return HttpResponseRedirect('/admin/user/sponsor/')

        return render(request, 'project_email_form.html', {
            'title': 'Send Project Presentation Email',
            'emails': ', '.join(emails),
            'action': 'project_presentation',
        })


email_admin_site = EmailAdminSite(name='email_admin')
