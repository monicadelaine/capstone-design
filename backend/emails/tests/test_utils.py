import pytest
from django.core import mail

from emails.models import EmailLog
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

    @pytest.mark.parametrize("field", ["smtp_host", "smtp_port", "smtp_username", "smtp_password"])
    def test_send_email_does_not_accept_smtp_credentials(self, field):
        with pytest.raises(TypeError):
            EmailClient().send_email(
                subject="Subject", message="Body", recipient_list=["a@example.com"], **{field: "x"}
            )
        assert EmailLog.objects.count() == 0

    def test_send_email_logs_a_successful_send(self):
        EmailClient().send_email(
            subject="Subject", message="Body", recipient_list=["a@example.com", "b@example.com"],
            kind=EmailLog.Kind.SPONSOR_OUTREACH, sent_by="admin@example.com",
        )

        assert len(mail.outbox) == 1
        log = EmailLog.objects.get()
        assert (log.kind, log.subject, log.sent_by, log.success, log.error) == (
            "sponsor_outreach", "Subject", "admin@example.com", True, "")
        assert log.recipients == ["a@example.com", "b@example.com"]
        assert log.sent_at is not None

    def test_send_email_logs_a_failure_and_reraises(self, monkeypatch):
        def broken(**kwargs):
            raise RuntimeError("smtp login failed")

        monkeypatch.setattr("emails.utils.send_mail", broken)

        with pytest.raises(RuntimeError, match="smtp login failed"):
            EmailClient().send_email(subject="Subject", message="Body", recipient_list="a@example.com")

        log = EmailLog.objects.get()
        assert (log.success, log.error, log.recipients) == (False, "smtp login failed", ["a@example.com"])

    def test_a_logging_problem_does_not_stop_the_email(self, monkeypatch):
        def broken_create(**kwargs):
            raise RuntimeError("database down")

        monkeypatch.setattr("emails.utils.EmailLog.objects.create", broken_create)

        EmailClient().send_email(subject="Subject", message="Body", recipient_list=["a@example.com"])

        assert len(mail.outbox) == 1

    def test_templated_senders_log_their_kind(self):
        client = EmailClient()
        client.send_sponsor_outreach(["a@example.com"], semester="fall", sent_by="admin")
        client.send_project_presentation(
            ["a@example.com"], date="d", time="t", project_name="p", project_description="x",
            contact_name="c", contact_email="c@example.com", zoom_details="z", sent_by="admin")

        assert list(EmailLog.objects.order_by("id").values_list("kind", "sent_by")) == [
            ("sponsor_outreach", "admin"), ("project_presentation", "admin")]

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

    def test_send_sponsor_outreach_uses_expected_subject(self, monkeypatch, settings):
        settings.CAPSTONE_YEAR = 2026
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
        assert calls[0]["subject"] == "UA CS Capstone Project Opportunity - Fall 2026"
        assert calls[0]["template_name"] == "sponsor_outreach"
        assert calls[0]["context"]["semester"] == "fall"

    def test_send_sponsor_outreach_year_overrides_setting(self, monkeypatch, settings):
        settings.CAPSTONE_YEAR = 2026
        client = EmailClient()
        calls = []
        monkeypatch.setattr(client, "send_templated_email", lambda **kwargs: calls.append(kwargs))

        client.send_sponsor_outreach(recipient_list=["sponsor@example.com"], semester="spring", year=2027)

        assert calls[0]["subject"] == "UA CS Capstone Project Opportunity - Spring 2027"

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
