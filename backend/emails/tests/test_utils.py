import pytest

from emails.utils import EmailClient


@pytest.mark.django_db
class TestEmailClient:
    def test_send_email_uses_send_mail_by_default(self, monkeypatch):
        client = EmailClient()
        calls = []

        def fake_send_mail(**kwargs):
            calls.append(kwargs)
            return 1

        monkeypatch.setattr("emails.utils.send_mail", fake_send_mail)

        client.send_email(
            subject="Subject",
            message="Body",
            recipient_list=["sponsor@example.com"],
            html_message="<p>Body</p>",
        )

        assert len(calls) == 1
        assert calls[0]["subject"] == "Subject"
        assert calls[0]["recipient_list"] == ["sponsor@example.com"]

    def test_send_email_wraps_string_recipient(self, monkeypatch):
        client = EmailClient()
        calls = []

        def fake_send_mail(**kwargs):
            calls.append(kwargs)
            return 1

        monkeypatch.setattr("emails.utils.send_mail", fake_send_mail)

        client.send_email(
            subject="Subject",
            message="Body",
            recipient_list="single@example.com",
        )

        assert len(calls) == 1
        assert calls[0]["recipient_list"] == ["single@example.com"]

    def test_send_email_uses_custom_smtp_when_credentials_provided(self, monkeypatch):
        client = EmailClient()
        smtp_calls = []
        email_instances = []

        class FakeEmail:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.alternatives = []
                self.sent = False
                email_instances.append(self)

            def attach_alternative(self, html, content_type):
                self.alternatives.append((html, content_type))

            def send(self, fail_silently=False):
                self.sent = True
                return 1

        def fake_smtp_backend(**kwargs):
            smtp_calls.append(kwargs)
            return object()

        monkeypatch.setattr("emails.utils.SMTPBackend", fake_smtp_backend)
        monkeypatch.setattr("emails.utils.EmailMultiAlternatives", FakeEmail)

        client.send_email(
            subject="Subject",
            message="Body",
            recipient_list=["a@example.com"],
            html_message="<p>Body</p>",
            smtp_host="smtp.example.com",
            smtp_port=2525,
            smtp_username="user",
            smtp_password="pass",
        )

        assert len(smtp_calls) == 1
        assert smtp_calls[0]["host"] == "smtp.example.com"
        assert smtp_calls[0]["port"] == 2525
        assert len(email_instances) == 1
        assert email_instances[0].kwargs["to"] == ["a@example.com"]
        assert email_instances[0].alternatives == [("<p>Body</p>", "text/html")]
        assert email_instances[0].sent is True

    def test_send_templated_email_renders_html_and_calls_send_email(self, monkeypatch):
        client = EmailClient()
        sent_calls = []

        monkeypatch.setattr(
            "emails.utils.render_to_string",
            lambda template, context: "<p>Hello <strong>World</strong></p>",
        )

        def fake_send_email(**kwargs):
            sent_calls.append(kwargs)
            return None

        monkeypatch.setattr(client, "send_email", fake_send_email)

        client.send_templated_email(
            subject="Subject",
            recipient_list=["sponsor@example.com"],
            template_name="sponsor_outreach",
            context={"semester": "fall"},
        )

        assert len(sent_calls) == 1
        assert sent_calls[0]["subject"] == "Subject"
        assert sent_calls[0]["recipient_list"] == ["sponsor@example.com"]
        assert sent_calls[0]["html_message"] == "<p>Hello <strong>World</strong></p>"
        assert sent_calls[0]["message"] == "Hello World"

    def test_send_sponsor_outreach_uses_expected_subject(self, monkeypatch):
        client = EmailClient()
        calls = []

        def fake_send_templated_email(**kwargs):
            calls.append(kwargs)
            return None

        monkeypatch.setattr(client, "send_templated_email", fake_send_templated_email)

        client.send_sponsor_outreach(
            recipient_list=["sponsor@example.com"],
            semester="fall",
            collection_date="Fall 2026 (9/20/26)",
        )

        assert len(calls) == 1
        assert calls[0]["subject"] == "UA CS Capstone Project Opportunity - Fall 2025"
        assert calls[0]["template_name"] == "sponsor_outreach"
        assert calls[0]["context"]["semester"] == "fall"

    def test_send_project_presentation_sets_subject_and_context(self, monkeypatch):
        client = EmailClient()
        calls = []

        def fake_send_templated_email(**kwargs):
            calls.append(kwargs)
            return None

        monkeypatch.setattr(client, "send_templated_email", fake_send_templated_email)

        client.send_project_presentation(
            recipient_list=["sponsor@example.com"],
            date="2026-10-10",
            time="10:00 AM",
            project_name="Design Manager",
            project_description="Portal",
            contact_name="Dr. Ada",
            contact_email="ada@example.com",
            zoom_details="https://zoom.us/j/123",
        )

        assert len(calls) == 1
        assert calls[0]["subject"] == "Project Presentation: Design Manager"
        assert calls[0]["template_name"] == "project_presentation"
        assert calls[0]["context"]["project_name"] == "Design Manager"

    def test_send_project_presentation_for_project_sets_project_context(self, monkeypatch):
        client = EmailClient()
        calls = []

        class ProjectStub:
            name = "Design Manager"

        def fake_send_templated_email(**kwargs):
            calls.append(kwargs)
            return None

        monkeypatch.setattr(client, "send_templated_email", fake_send_templated_email)

        client.send_project_presentation_for_project(
            recipient_list=["sponsor@example.com"],
            date="2026-10-10",
            time="10:00 AM",
            project=ProjectStub(),
            zoom_details="https://zoom.us/j/123",
        )

        assert len(calls) == 1
        assert calls[0]["subject"] == "Project Presentation: Design Manager"
        assert calls[0]["template_name"] == "project_presentation_single"
        assert calls[0]["context"]["project"].name == "Design Manager"

    def test_render_project_presentation_single_html_uses_single_template(self, monkeypatch):
        client = EmailClient()
        calls = []

        def fake_render_to_string(template_name, context):
            calls.append((template_name, context))
            return "<p>Single project presentation</p>"

        monkeypatch.setattr("emails.utils.render_to_string", fake_render_to_string)

        result = client.render_project_presentation_single_html(
            date="2026-10-10",
            time="10:00 AM",
            project=object(),
            zoom_details="https://zoom.us/j/123",
        )

        assert result == "<p>Single project presentation</p>"
        assert len(calls) == 1
        assert calls[0][0] == "emails/project_presentation_single.html"
        assert calls[0][1]["zoom_details"] == "https://zoom.us/j/123"

    def test_convert_html_to_mhtml_wraps_content(self):
        client = EmailClient()

        result = client.convert_html_to_mhtml("<p>Body</p>")

        assert "MIME-Version: 1.0" in result
        assert "<p>Body</p>" in result
        assert "multipart/related" in result

    def test_convert_html_to_eml_includes_headers(self):
        client = EmailClient()

        result = client.convert_html_to_eml(
            "<p>Body</p>",
            subject="Hello",
            to_email="sponsor@example.com",
        )

        assert "Subject: Hello" in result
        assert "To: sponsor@example.com" in result
        assert "<p>Body</p>" in result
