import pytest

from user.models import Sponsor, Student
from user.serializers import SponsorSerializer, StudentSerializer


@pytest.fixture
def sponsor_data():
    return {
        "first_name": "Alice",
        "last_name": "Walker",
        "email": "alice@example.com",
    }


@pytest.fixture
def sample_sponsor(db, sponsor_data):
    return Sponsor.objects.create(**sponsor_data)


@pytest.fixture
def student_data():
    return {
        "cwid": "12345678",
        "first_name": "Bob",
        "last_name": "Smith",
        "email": "bob@example.com",
    }


@pytest.fixture
def sample_student(db, student_data):
    return Student.objects.create(**student_data)


@pytest.mark.django_db
class TestSponsorSerializer:
    def test_serializes_sponsor_fields(self, sample_sponsor):
        serializer = SponsorSerializer(instance=sample_sponsor)

        assert serializer.data["id"] == sample_sponsor.id
        assert serializer.data["first_name"] == "Alice"
        assert serializer.data["last_name"] == "Walker"
        assert serializer.data["email"] == "alice@example.com"
        assert serializer.data["projects_allowed"] == 3

    def test_creates_sponsor_with_required_fields(self, sponsor_data):
        serializer = SponsorSerializer(data=sponsor_data)

        assert serializer.is_valid(), serializer.errors
        sponsor = serializer.save()

        assert sponsor.first_name == sponsor_data["first_name"]
        assert sponsor.last_name == sponsor_data["last_name"]
        assert sponsor.email == sponsor_data["email"]
        assert sponsor.projects_allowed == 3

    def test_rejects_invalid_phone_number(self, sponsor_data):
        serializer = SponsorSerializer(
            data={
                **sponsor_data,
                "phone_number": "invalid-phone",
            }
        )

        assert not serializer.is_valid()
        assert "phone_number" in serializer.errors


@pytest.mark.django_db
class TestStudentSerializer:
    def test_serializes_student_fields(self, sample_student):
        serializer = StudentSerializer(instance=sample_student)

        assert serializer.data["id"] == sample_student.id
        assert serializer.data["cwid"] == "12345678"
        assert serializer.data["first_name"] == "Bob"
        assert serializer.data["last_name"] == "Smith"
        assert serializer.data["email"] == "bob@example.com"

    def test_creates_student_with_required_fields(self, student_data):
        serializer = StudentSerializer(data=student_data)

        assert serializer.is_valid(), serializer.errors
        student = serializer.save()

        assert student.cwid == student_data["cwid"]
        assert student.first_name == student_data["first_name"]
        assert student.last_name == student_data["last_name"]
        assert student.email == student_data["email"]

    def test_rejects_invalid_cwid(self, student_data):
        serializer = StudentSerializer(
            data={
                **student_data,
                "cwid": "1234ABCD",
            }
        )

        assert not serializer.is_valid()
        assert "cwid" in serializer.errors

    def test_rejects_duplicate_cwid(self, sample_student, student_data):
        serializer = StudentSerializer(
            data={
                **student_data,
                "cwid": sample_student.cwid,
                "email": "new.email@example.com",
            }
        )

        assert not serializer.is_valid()
        assert "cwid" in serializer.errors
