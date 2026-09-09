import pytest

from emails.serializers import EmailSerializer


@pytest.mark.django_db
class TestEmailSerializer:
    def test_valid_payload(self):
        payload = {
            "subject": "Subject",
            "message": "Message body",
            "recipients": ["alice@example.com", "bob@example.com"],
            "html_message": "<p>Message body</p>",
        }

        serializer = EmailSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["subject"] == payload["subject"]
        assert serializer.validated_data["message"] == payload["message"]
        assert serializer.validated_data["recipients"] == payload["recipients"]
        assert serializer.validated_data["html_message"] == payload["html_message"]

    def test_rejects_empty_recipients(self):
        payload = {
            "subject": "Subject",
            "message": "Message body",
            "recipients": [],
        }

        serializer = EmailSerializer(data=payload)

        assert not serializer.is_valid()
        assert "recipients" in serializer.errors

    def test_rejects_invalid_email_address(self):
        payload = {
            "subject": "Subject",
            "message": "Message body",
            "recipients": ["not-an-email"],
        }

        serializer = EmailSerializer(data=payload)

        assert not serializer.is_valid()
        assert "recipients" in serializer.errors

    def test_html_message_is_optional(self):
        payload = {
            "subject": "Subject",
            "message": "Message body",
            "recipients": ["alice@example.com"],
        }

        serializer = EmailSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors
        assert "html_message" not in serializer.validated_data
