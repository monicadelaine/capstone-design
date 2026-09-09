from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.template.loader import render_to_string


class EmailClient:
    def __init__(self):
        self.default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    def send_email(self, subject, message, recipient_list, from_email=None, html_message=None,
                   smtp_host=None, smtp_port=None, smtp_username=None, smtp_password=None):
        from_email = from_email or self.default_from_email

        if isinstance(recipient_list, str):
            recipient_list = [recipient_list]

        use_custom_smtp = smtp_host and smtp_username and smtp_password

        if use_custom_smtp:
            connection = SMTPBackend(
                host=smtp_host,
                port=int(smtp_port) if smtp_port else 587,
                username=smtp_username,
                password=smtp_password,
                use_tls=True,
                fail_silently=getattr(settings, 'EMAIL_FAIL_SILENTLY', False),
            )
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list,
                connection=connection,
            )
            if html_message:
                email.attach_alternative(html_message, 'text/html')
            email.send(fail_silently=getattr(settings, 'EMAIL_FAIL_SILENTLY', False))
        else:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=getattr(settings, 'EMAIL_FAIL_SILENTLY', False),
            )

    def send_templated_email(self, subject, recipient_list, template_name, context=None,
                             from_email=None, smtp_host=None, smtp_port=None,
                             smtp_username=None, smtp_password=None):
        context = context or {}
        
        html_content = render_to_string(f'emails/{template_name}.html', context)
        
        # For text version, strip HTML tags from HTML content
        import re
        text_content = re.sub(r'<[^>]+>', '', html_content)
        text_content = re.sub(r'\n\s*\n', '\n', text_content).strip()

        return self.send_email(
            subject=subject,
            message=text_content,
            recipient_list=recipient_list,
            html_message=html_content,
            from_email=from_email,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
        )

    def send_sponsor_outreach(self, recipient_list, semester='spring', collection_date='Spring 2025 (1/14/25)',
                              from_email=None, smtp_host=None, smtp_port=None,
                              smtp_username=None, smtp_password=None):
        return self.send_templated_email(
            subject=f"UA CS Capstone Project Opportunity - {semester.capitalize()} 2025",
            recipient_list=recipient_list,
            template_name="sponsor_outreach",
            context={
                'semester': semester.lower(),
                'collection_date': collection_date,
            },
            from_email=from_email,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
        )

    def send_project_presentation(
        self,
        recipient_list,
        date,
        time,
        project_name,
        project_description,
        contact_name,
        contact_email,
        zoom_details,
        projects=None,
        from_email=None,
        smtp_host=None,
        smtp_port=None,
        smtp_username=None,
        smtp_password=None,
    ):
        return self.send_templated_email(
            subject=f"Project Presentation: {project_name}",
            recipient_list=recipient_list,
            template_name="project_presentation",
            context={
                'date': date,
                'time': time,
                'project_name': project_name,
                'project_description': project_description,
                'contact_name': contact_name,
                'contact_email': contact_email,
                'zoom_details': zoom_details,
                'projects': projects or [],
            },
            from_email=from_email,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
        )

    def send_project_presentation_for_project(
        self,
        recipient_list,
        date,
        time,
        project,
        zoom_details,
        from_email=None,
        smtp_host=None,
        smtp_port=None,
        smtp_username=None,
        smtp_password=None,
    ):
        return self.send_templated_email(
            subject=f"Project Presentation: {project.name}",
            recipient_list=recipient_list,
            template_name="project_presentation_single",
            context={
                'date': date,
                'time': time,
                'project': project,
                'zoom_details': zoom_details,
            },
            from_email=from_email,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
        )

    def render_sponsor_outreach_html(self, semester='spring', collection_date='TBD'):
        context = {
            'semester': semester.lower(),
            'collection_date': collection_date,
        }
        return render_to_string('emails/sponsor_outreach.html', context)

    def render_project_presentation_html(self, date='TBD', time='TBD', project_name='TBD',
                                         project_description='TBD', contact_name='TBD',
                                         contact_email='TBD', zoom_details='TBD', projects=None):
        context = {
            'date': date,
            'time': time,
            'project_name': project_name,
            'project_description': project_description,
            'contact_name': contact_name,
            'contact_email': contact_email,
            'zoom_details': zoom_details,
            'projects': projects or [],
        }
        return render_to_string('emails/project_presentation.html', context)

    def render_project_presentation_single_html(self, date='TBD', time='TBD', project=None, zoom_details='TBD'):
        context = {
            'date': date,
            'time': time,
            'project': project,
            'zoom_details': zoom_details,
        }
        return render_to_string('emails/project_presentation_single.html', context)

    def convert_html_to_mhtml(self, html_content, title='Email'):
        mhtml_header = f"""MIME-Version: 1.0
Content-Type: multipart/related; boundary="----=_Part_0_12345678.12345678"

------=_Part_0_12345678.12345678
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: 7bit

"""
        mhtml_footer = """

------=_Part_0_12345678.12345678--
"""
        return mhtml_header + html_content + mhtml_footer

    def convert_html_to_eml(self, html_content, subject='Project Presentation', to_email=''):
        eml_content = f"""Subject: {subject}
To: {to_email}
X-Unsent: 1
MIME-Version: 1.0
Content-Type: text/html; charset="utf-8"

{html_content}"""
        return eml_content


email_client = EmailClient()
