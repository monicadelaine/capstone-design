import pytest
from django.contrib import messages
from django.http import HttpResponse
from django.test import RequestFactory

from emails.admin import EmailAdminSite


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def admin_site():
    return EmailAdminSite(name="email_admin")


@pytest.fixture
def admin_user(db):
    from django.contrib.auth.models import User

    return User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="testpass123",
    )


@pytest.mark.django_db
class TestEmailAdminSiteViews:
    def test_get_urls_includes_custom_actions(self, admin_site):
        urls = admin_site.get_urls()
        names = {url.name for url in urls if getattr(url, "name", None)}

        assert "send_sponsor_outreach" in names
        assert "send_project_presentation" in names

    def test_send_sponsor_outreach_view_get_renders_form(self, rf, admin_site, admin_user, monkeypatch):
        request = rf.get("/?emails=alice@example.com, bob@example.com")
        request.user = admin_user
        captured = {}

        def fake_render(request, template_name, context):
            captured["template_name"] = template_name
            captured["context"] = context
            return HttpResponse("rendered")

        monkeypatch.setattr("emails.admin.render", fake_render)

        response = admin_site.send_sponsor_outreach_view(request)

        assert response.status_code == 200
        assert captured["template_name"] == "email_form.html"
        assert captured["context"]["emails"] == "alice@example.com, bob@example.com"

    def test_send_sponsor_outreach_view_posts_and_redirects(self, rf, admin_site, admin_user, monkeypatch):
        request = rf.post("/?emails=alice@example.com,bob@example.com",
                          {"semester": "fall", "collection_date": "Fall 2026 (9/20/26)"})
        request.user = admin_user
        sent_calls = []
        success_calls = []

        def fake_send_sponsor_outreach(**kwargs):
            sent_calls.append(kwargs)

        monkeypatch.setattr("emails.utils.email_client.send_sponsor_outreach", fake_send_sponsor_outreach)
        monkeypatch.setattr("django.contrib.messages.success", lambda request, message: success_calls.append(message))

        response = admin_site.send_sponsor_outreach_view(request)

        assert response.status_code == 302
        assert sent_calls[0]["recipient_list"] == ["alice@example.com", "bob@example.com"]
        assert success_calls == ["Successfully sent outreach email to 2 sponsor(s)."]

    def test_send_project_presentation_view_posts_one_email_per_recipient(self, rf, admin_site, admin_user, monkeypatch):
        request = rf.post(
            "/?emails=alice@example.com,bob@example.com",
            {
                "date": "2026-10-10",
                "time": "10:00 AM",
                "project_name": "Design Manager",
                "project_description": "Portal",
                "contact_name": "Dr. Ada",
                "contact_email": "ada@example.com",
                "zoom_details": "https://zoom.us/j/123",
            },
        )
        request.user = admin_user
        sent_calls = []
        success_calls = []

        def fake_send_project_presentation(**kwargs):
            sent_calls.append(kwargs)

        monkeypatch.setattr("emails.utils.email_client.send_project_presentation", fake_send_project_presentation)
        monkeypatch.setattr("django.contrib.messages.success", lambda request, message: success_calls.append(message))

        response = admin_site.send_project_presentation_view(request)

        assert response.status_code == 302
        assert len(sent_calls) == 2
        assert {call["recipient_list"][0] for call in sent_calls} == {"alice@example.com", "bob@example.com"}
        assert success_calls == ["Successfully sent presentation email to 2 sponsor(s)."]

    def test_send_project_presentation_view_get_renders_form(self, rf, admin_site, admin_user, monkeypatch):
        request = rf.get("/?emails=alice@example.com")
        request.user = admin_user
        captured = {}

        def fake_render(request, template_name, context):
            captured["template_name"] = template_name
            captured["context"] = context
            return HttpResponse("rendered")

        monkeypatch.setattr("emails.admin.render", fake_render)

        response = admin_site.send_project_presentation_view(request)

        assert response.status_code == 200
        assert captured["template_name"] == "project_email_form.html"
        assert captured["context"]["emails"] == "alice@example.com"
