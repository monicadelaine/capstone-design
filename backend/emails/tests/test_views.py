import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client(db):
    """Create an authenticated API client for testing."""
    client = APIClient()
    user = User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="testpass123",
    )
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestSendEmailView:
    def test_get_send_email_returns_serializer_shape(self, api_client):
        url = reverse("emails:send_email")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "subject" in response.data
        assert "message" in response.data
        assert "recipients" in response.data

    def test_post_send_email_success(self, api_client, monkeypatch):
        url = reverse("emails:send_email")
        payload = {
            "subject": "Capstone update",
            "message": "Project is on track.",
            "recipients": ["sponsor@example.com"],
            "html_message": "<p>Project is on track.</p>",
        }
        calls = []

        def fake_send_email(**kwargs):
            calls.append(kwargs)

        monkeypatch.setattr("emails.views.email_client.send_email", fake_send_email)

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "email sent successfully"
        assert len(calls) == 1
        assert calls[0]["subject"] == payload["subject"]
        assert calls[0]["recipient_list"] == payload["recipients"]

    def test_post_send_email_rejects_invalid_payload(self, api_client):
        url = reverse("emails:send_email")
        payload = {
            "subject": "Capstone update",
            "message": "Project is on track.",
            "recipients": ["not-an-email"],
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "recipients" in response.data

    def test_post_send_email_handles_exception(self, api_client, monkeypatch):
        url = reverse("emails:send_email")
        payload = {
            "subject": "Capstone update",
            "message": "Project is on track.",
            "recipients": ["sponsor@example.com"],
        }

        def raise_error(**kwargs):
            raise RuntimeError("smtp unavailable")

        monkeypatch.setattr("emails.views.email_client.send_email", raise_error)

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data["error"] == "smtp unavailable"


@pytest.mark.django_db
class TestSendSponsorOutreachView:
    def test_send_sponsor_outreach_success(self, api_client, monkeypatch):
        url = reverse("emails:send_sponsor_outreach")
        payload = {
            "recipients": ["alice@example.com", "bob@example.com"],
            "semester": "fall",
            "collection_date": "Fall 2026 (9/20/26)",
            "from_email": "faculty@example.com",
        }
        calls = []

        def fake_send_sponsor_outreach(**kwargs):
            calls.append(kwargs)

        monkeypatch.setattr(
            "emails.views.email_client.send_sponsor_outreach",
            fake_send_sponsor_outreach,
        )

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "sponsor outreach email sent successfully"
        assert len(calls) == 1
        assert calls[0]["recipient_list"] == payload["recipients"]
        assert calls[0]["semester"] == payload["semester"]

    def test_send_sponsor_outreach_accepts_csv_recipients(self, api_client, monkeypatch):
        url = reverse("emails:send_sponsor_outreach")
        payload = {
            "recipients": "alice@example.com, bob@example.com",
        }
        calls = []

        def fake_send_sponsor_outreach(**kwargs):
            calls.append(kwargs)

        monkeypatch.setattr(
            "emails.views.email_client.send_sponsor_outreach",
            fake_send_sponsor_outreach,
        )

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert calls[0]["recipient_list"] == ["alice@example.com", "bob@example.com"]

    def test_send_sponsor_outreach_requires_recipients(self, api_client):
        url = reverse("emails:send_sponsor_outreach")

        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "recipients are required"


@pytest.mark.django_db
class TestSendProjectPresentationView:
    def test_send_project_presentation_success(self, api_client, monkeypatch):
        url = reverse("emails:send_project_presentation")
        payload = {
            "recipients": ["sponsor@example.com"],
            "date": "2026-10-10",
            "time": "10:00 AM",
            "project_name": "Design Manager",
            "project_description": "A project lifecycle portal.",
            "contact_name": "Dr. Ada",
            "contact_email": "ada@example.com",
            "zoom_details": "https://zoom.us/j/123",
        }
        calls = []

        def fake_send_project_presentation(**kwargs):
            calls.append(kwargs)

        monkeypatch.setattr(
            "emails.views.email_client.send_project_presentation",
            fake_send_project_presentation,
        )

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "project presentation email sent successfully"
        assert len(calls) == 1
        assert calls[0]["project_name"] == payload["project_name"]

    def test_send_project_presentation_requires_fields(self, api_client):
        url = reverse("emails:send_project_presentation")
        payload = {
            "recipients": ["sponsor@example.com"],
            "date": "2026-10-10",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "time is required"

    def test_send_project_presentation_handles_exception(self, api_client, monkeypatch):
        url = reverse("emails:send_project_presentation")
        payload = {
            "recipients": ["sponsor@example.com"],
            "date": "2026-10-10",
            "time": "10:00 AM",
            "project_name": "Design Manager",
            "project_description": "A project lifecycle portal.",
            "contact_name": "Dr. Ada",
            "contact_email": "ada@example.com",
            "zoom_details": "https://zoom.us/j/123",
        }

        def raise_error(**kwargs):
            raise RuntimeError("template rendering failed")

        monkeypatch.setattr(
            "emails.views.email_client.send_project_presentation",
            raise_error,
        )

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data["error"] == "template rendering failed"
