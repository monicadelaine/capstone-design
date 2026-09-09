import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.models import Sponsor, Student


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
def sample_student(db):
    return Student.objects.create(
        cwid="12345678",
        first_name="Bob",
        last_name="Smith",
        email="bob@example.com",
        class_code=Student.Class.SENIOR,
        major_code="CS",
    )


@pytest.mark.django_db
class TestSponsorViewSet:
    def test_list_sponsors(self, api_client, sample_sponsor):
        url = reverse("user:sponsor-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == sample_sponsor.id

    def test_create_sponsor(self, api_client):
        url = reverse("user:sponsor-list")
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "organization": "Acme Inc",
            "phone_number": "123-456-7890",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Sponsor.objects.filter(email="john.doe@example.com").exists()

    def test_retrieve_sponsor(self, api_client, sample_sponsor):
        url = reverse("user:sponsor-detail", kwargs={"pk": sample_sponsor.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == sample_sponsor.email

    def test_update_sponsor(self, api_client, sample_sponsor):
        url = reverse("user:sponsor-detail", kwargs={"pk": sample_sponsor.id})
        payload = {"organization": "Updated Org"}
        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        sample_sponsor.refresh_from_db()
        assert sample_sponsor.organization == "Updated Org"

    def test_delete_sponsor(self, api_client, sample_sponsor):
        url = reverse("user:sponsor-detail", kwargs={"pk": sample_sponsor.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert not Sponsor.objects.filter(pk=sample_sponsor.id).exists()

    def test_create_sponsor_rejects_invalid_phone(self, api_client):
        url = reverse("user:sponsor-list")
        payload = {
            "first_name": "Invalid",
            "last_name": "Phone",
            "email": "invalid.phone@example.com",
            "phone_number": "not-a-number",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone_number" in response.data


@pytest.mark.django_db
class TestStudentViewSet:
    def test_list_students(self, api_client, sample_student):
        url = reverse("user:student-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == sample_student.id

    def test_create_student(self, api_client):
        url = reverse("user:student-list")
        payload = {
            "cwid": "87654321",
            "first_name": "Jane",
            "last_name": "Taylor",
            "email": "jane.taylor@example.com",
            "class_code": Student.Class.JUNIOR,
            "major_code": "CS",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Student.objects.filter(cwid="87654321").exists()

    def test_retrieve_student(self, api_client, sample_student):
        url = reverse("user:student-detail", kwargs={"pk": sample_student.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["cwid"] == sample_student.cwid

    def test_update_student(self, api_client, sample_student):
        url = reverse("user:student-detail", kwargs={"pk": sample_student.id})
        payload = {"preferred_name": "Bobby"}
        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        sample_student.refresh_from_db()
        assert sample_student.preferred_name == "Bobby"

    def test_delete_student(self, api_client, sample_student):
        url = reverse("user:student-detail", kwargs={"pk": sample_student.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert not Student.objects.filter(pk=sample_student.id).exists()

    def test_create_student_rejects_invalid_cwid(self, api_client):
        url = reverse("user:student-list")
        payload = {
            "cwid": "12AB5678",
            "first_name": "Invalid",
            "last_name": "CWID",
            "email": "invalid.cwid@example.com",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cwid" in response.data

    def test_create_student_rejects_duplicate_cwid(self, api_client, sample_student):
        url = reverse("user:student-list")
        payload = {
            "cwid": sample_student.cwid,
            "first_name": "Dup",
            "last_name": "Student",
            "email": "dup.student@example.com",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cwid" in response.data
