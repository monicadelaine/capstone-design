import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from user.models import Sponsor, Student


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Sponsor tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSponsorCreation:
    def test_creates_with_required_fields(self, sponsor_data):
        sponsor = Sponsor.objects.create(**sponsor_data)
        assert sponsor.pk is not None
        assert sponsor.first_name == "Alice"
        assert sponsor.last_name == "Walker"
        assert sponsor.email == "alice@example.com"

    def test_default_projects_allowed(self, sample_sponsor):
        assert sample_sponsor.projects_allowed == 3

    def test_optional_fields_default_to_none(self, sample_sponsor):
        assert sample_sponsor.organization is None
        assert sample_sponsor.phone_number is None

    def test_optional_fields_can_be_set(self, db, sponsor_data):
        sponsor = Sponsor.objects.create(
            **sponsor_data,
            organization="Tech Corp",
            phone_number="(123) 456-7890",
        )
        assert sponsor.organization == "Tech Corp"
        assert sponsor.phone_number == "(123) 456-7890"

    def test_created_at_is_set_on_creation(self, sample_sponsor):
        assert sample_sponsor.created_at is not None

    def test_updated_at_is_set_on_creation(self, sample_sponsor):
        assert sample_sponsor.updated_at is not None

    def test_updated_at_changes_on_save(self, sample_sponsor):
        original = sample_sponsor.updated_at
        sample_sponsor.first_name = "Updated"
        sample_sponsor.save()
        assert sample_sponsor.updated_at >= original


@pytest.mark.django_db
class TestSponsorStringRepresentation:
    def test_str_returns_full_name(self, sample_sponsor):
        assert str(sample_sponsor) == "Alice Walker"

    def test_name_method_returns_full_name(self, sample_sponsor):
        assert sample_sponsor.name() == "Alice Walker"


@pytest.mark.django_db
class TestSponsorPhoneValidation:
    def _make_sponsor(self, phone):
        sponsor = Sponsor(
            first_name="Alice",
            last_name="Walker",
            email="alice@example.com",
            phone_number=phone,
        )
        sponsor.full_clean()
        return sponsor

    @pytest.mark.parametrize("phone", [
        "(123) 456-7890",
        "123-456-7890",
        "123.456.7890",
        "+1 (123) 456-7890",
        "+1 123-456-7890",
    ])
    def test_valid_phone_numbers(self, db, phone):
        sponsor = self._make_sponsor(phone)
        assert sponsor.phone_number == phone

    @pytest.mark.parametrize("phone", [
        "123",
        "abcdefghij",
        "123-45-6789",
        "12345678901234567",
    ])
    def test_invalid_phone_numbers_raise_validation_error(self, db, phone):
        with pytest.raises(ValidationError):
            self._make_sponsor(phone)


# ---------------------------------------------------------------------------
# Student tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStudentCreation:
    def test_creates_with_required_fields(self, student_data):
        student = Student.objects.create(**student_data)
        assert student.pk is not None
        assert student.cwid == "12345678"
        assert student.first_name == "Bob"
        assert student.last_name == "Smith"
        assert student.email == "bob@example.com"

    def test_optional_fields_default_to_none(self, sample_student):
        assert sample_student.middle_name is None
        assert sample_student.preferred_name is None
        assert sample_student.description is None
        assert sample_student.class_code is None
        assert sample_student.major_code is None

    def test_optional_fields_can_be_set(self, db, student_data):
        student = Student.objects.create(
            **student_data,
            middle_name="Lee",
            preferred_name="Bobby",
            description="Skilled in Python",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )
        assert student.middle_name == "Lee"
        assert student.preferred_name == "Bobby"
        assert student.description == "Skilled in Python"
        assert student.class_code == Student.Class.SENIOR
        assert student.major_code == "CS"

    def test_created_at_is_set_on_creation(self, sample_student):
        assert sample_student.created_at is not None

    def test_updated_at_is_set_on_creation(self, sample_student):
        assert sample_student.updated_at is not None

    def test_updated_at_changes_on_save(self, sample_student):
        original = sample_student.updated_at
        sample_student.first_name = "Updated"
        sample_student.save()
        assert sample_student.updated_at >= original


@pytest.mark.django_db
class TestStudentStringRepresentation:
    def test_str_returns_full_name(self, sample_student):
        assert str(sample_student) == "Bob Smith"

    def test_name_method_returns_full_name(self, sample_student):
        assert sample_student.name() == "Bob Smith"


@pytest.mark.django_db
class TestStudentCwidValidation:
    def _make_student(self, cwid):
        student = Student(
            cwid=cwid,
            first_name="Bob",
            last_name="Smith",
            email="bob@example.com",
        )
        student.full_clean()
        return student

    def test_valid_cwid(self, db):
        student = self._make_student("00000001")
        assert student.cwid == "00000001"

    @pytest.mark.parametrize("cwid", [
        "1234567",    # 7 digits (too short)
        "123456789",  # 9 digits (too long)
        "1234567a",   # contains letter
        "1234 678",   # contains space
    ])
    def test_invalid_cwid_raises_validation_error(self, db, cwid):
        with pytest.raises(ValidationError):
            self._make_student(cwid)

    def test_cwid_must_be_unique(self, db, student_data):
        Student.objects.create(**student_data)
        with pytest.raises(IntegrityError):
            Student.objects.create(
                cwid=student_data["cwid"],
                first_name="Other",
                last_name="Person",
                email="other@example.com",
            )


@pytest.mark.django_db
class TestStudentClassChoices:
    @pytest.mark.parametrize("code,label", [
        ("FR", "Freshman"),
        ("SO", "Sophomore"),
        ("JR", "Junior"),
        ("SR", "Senior"),
        ("GR", "Graduate"),
    ])
    def test_valid_class_codes(self, db, code, label):
        student = Student.objects.create(
            cwid=f"700000{Student.Class.values.index(code):02d}",
            first_name="Test",
            last_name="Student",
            email="test@example.com",
            class_code=code,
        )
        assert student.class_code == code
        assert student.get_class_code_display() == label
