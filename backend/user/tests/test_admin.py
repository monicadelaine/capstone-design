import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import RequestFactory

from project.models import Attachment, Project
from user.admin import SponsorAdmin
from user.models import Sponsor


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="testpass123",
    )


@pytest.fixture
def sample_sponsor(db):
    return Sponsor.objects.create(
        first_name="Alice",
        last_name="Walker",
        email="alice@example.com",
        organization="Tech Corp",
        phone_number="(123) 456-7890",
    )


@pytest.fixture
def second_sponsor(db):
    return Sponsor.objects.create(
        first_name="Bob",
        last_name="Jones",
        email="bob@example.com",
        organization="Other Org",
        phone_number="(321) 654-0987",
    )


@pytest.fixture
def sample_project(db, sample_sponsor):
    return Project.objects.create(
        name="Test Project",
        sponsor=sample_sponsor,
    )


@pytest.mark.django_db
class TestSponsorAdminActions:
    def test_send_sponsor_outreach_email_posts_to_email_client(self, rf, admin_user, sample_sponsor, monkeypatch):
        admin_instance = SponsorAdmin(Sponsor, admin.site)
        request = rf.post("/", {"semester": "fall", "collection_date": "Fall 2026 (9/20/26)"})
        request.user = admin_user
        sent_calls = []
        redirects = []

        def fake_send_sponsor_outreach(**kwargs):
            sent_calls.append(kwargs)

        monkeypatch.setattr("user.admin.email_client.send_sponsor_outreach", fake_send_sponsor_outreach)
        monkeypatch.setattr("user.admin.HttpResponseRedirect",
                            lambda url: redirects.append(url) or HttpResponse(status=302))
        admin_instance.message_user = lambda *args, **kwargs: None

        response = admin_instance.send_sponsor_outreach_email(request, Sponsor.objects.filter(pk=sample_sponsor.pk))

        assert response.status_code == 302
        assert sent_calls[0]["recipient_list"] == [sample_sponsor.email]
        assert sent_calls[0]["semester"] == "fall"
        assert redirects == ["/admin/user/sponsor/"]

    def test_export_sponsor_outreach_eml_creates_attachment(self, rf, admin_user, sample_sponsor, monkeypatch):
        admin_instance = SponsorAdmin(Sponsor, admin.site)
        request = rf.post("/", {"semester": "fall", "collection_date": "Fall 2026 (9/20/26)", "create_btn": "1"})
        request.user = admin_user
        messages = []

        monkeypatch.setattr("user.admin.email_client.render_sponsor_outreach_html",
                            lambda semester, collection_date: "<p>HTML</p>")
        monkeypatch.setattr("user.admin.email_client.convert_html_to_eml", lambda html_content,
                            subject, to_email: f"{subject}\n{to_email}\n{html_content}")
        admin_instance.message_user = lambda request, message, level=None, extra_tags=None: messages.append(
            (message, level, extra_tags))

        response = admin_instance.export_sponsor_outreach_eml(request, Sponsor.objects.filter(pk=sample_sponsor.pk))

        assert response.status_code == 302
        attachment = Attachment.objects.get(title="Sponsor Outreach Email - Fall Fall 2026 (9/20/26)")
        assert attachment.content.startswith("UA CS Capstone Project Opportunity - Fall")
        assert "<p>HTML</p>" in attachment.content
        assert messages and "Download" in messages[0][0]

    def test_send_project_presentation_email_sends_for_each_project(self, rf, admin_user, sample_sponsor, sample_project, monkeypatch):
        second_project = Project.objects.create(name="Second Project", sponsor=sample_sponsor)
        admin_instance = SponsorAdmin(Sponsor, admin.site)
        request = rf.post("/", {"date": "2026-10-10", "time": "10:00 AM", "zoom_details": "Zoom"})
        request.user = admin_user
        sent_calls = []
        admin_instance.message_user = lambda *args, **kwargs: None

        def fake_send_project_presentation_for_project(**kwargs):
            sent_calls.append(kwargs)

        monkeypatch.setattr("user.admin.email_client.send_project_presentation_for_project",
                            fake_send_project_presentation_for_project)

        response = admin_instance.send_project_presentation_email(request, Sponsor.objects.filter(pk=sample_sponsor.pk))

        assert response.status_code == 302
        assert len(sent_calls) == 2
        assert {call["project"].id for call in sent_calls} == {sample_project.id, second_project.id}

    def test_export_project_presentation_eml_creates_one_attachment_per_project(self, rf, admin_user, sample_sponsor, sample_project, monkeypatch):
        second_project = Project.objects.create(name="Second Project", sponsor=sample_sponsor)
        admin_instance = SponsorAdmin(Sponsor, admin.site)
        request = rf.post("/", {"date": "2026-10-10", "time": "10:00 AM", "zoom_details": "Zoom", "create_btn": "1"})
        request.user = admin_user
        messages = []

        monkeypatch.setattr("user.admin.email_client.render_project_presentation_single_html",
                            lambda **kwargs: "<p>Preview</p>")
        monkeypatch.setattr("user.admin.email_client.convert_html_to_eml", lambda html_content,
                            subject, to_email: f"{subject}\n{to_email}\n{html_content}")
        admin_instance.message_user = lambda request, message, level=None: messages.append((message, level))

        response = admin_instance.export_project_presentation_eml(request, Sponsor.objects.filter(pk=sample_sponsor.pk))

        assert response.status_code == 302
        assert Attachment.objects.filter(title="Project Presentation - Test Project").exists()
        assert Attachment.objects.filter(title="Project Presentation - Second Project").exists()
        assert messages == [("Created 2 EML file(s)", "info")]


@pytest.mark.django_db
class TestSponsorAdminRenderFlows:
    def test_export_sponsor_outreach_preview_renders_template(self, rf, admin_user, sample_sponsor, monkeypatch):
        admin_instance = SponsorAdmin(Sponsor, admin.site)
        request = rf.post("/", {"semester": "spring", "collection_date": "TBD", "preview_btn": "1"})
        request.user = admin_user
        captured = {}

        def fake_render(request, template_name, context):
            captured["template_name"] = template_name
            captured["context"] = context
            return HttpResponse("rendered")

        monkeypatch.setattr("user.admin.render", fake_render)

        response = admin_instance.export_sponsor_outreach_eml(request, Sponsor.objects.filter(pk=sample_sponsor.pk))

        assert response.status_code == 200
        assert captured["template_name"] == "admin/export_sponsor_outreach.html"
        assert captured["context"]["semester"] == "spring"

    def test_send_sponsor_outreach_email_get_renders_form(self, rf, admin_user, sample_sponsor, monkeypatch):
        admin_instance = SponsorAdmin(Sponsor, admin.site)
        request = rf.get("/?emails=alice@example.com")
        request.user = admin_user
        captured = {}

        def fake_render(request, template_name, context):
            captured["template_name"] = template_name
            captured["context"] = context
            return HttpResponse("rendered")

        monkeypatch.setattr("user.admin.render", fake_render)

        response = admin_instance.send_sponsor_outreach_email(request, Sponsor.objects.filter(pk=sample_sponsor.pk))

        assert response.status_code == 200
        assert captured["template_name"] == "admin/sponsor_outreach_action.html"
        assert captured["context"]["selected_ids"] == [sample_sponsor.id]
