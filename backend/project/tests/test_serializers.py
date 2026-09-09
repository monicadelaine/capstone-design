from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.utils import timezone
from django.utils.text import slugify

from project.models import (
    MAX_ATTACHMENT_FILE_SIZE,
    Attachment,
    Assignment,
    Feedback,
    Preference,
    Project,
    Semester,
)
from project.serializers import (
    AttachmentSerializer,
    AssignmentSerializer,
    FeedbackSerializer,
    PreferenceSerializer,
    ProjectSerializer,
    SemesterSerializer,
)
from user.models import Sponsor, Student


@pytest.fixture
def sample_sponsor(db):
    return Sponsor.objects.create(
        email="sponsor@example.com",
        first_name="John",
        last_name="Doe",
        organization="Tech Corp",
        phone_number="(123) 456-7890",
    )


@pytest.fixture
def sample_student(db):
    return Student.objects.create(
        cwid="12345678",
        email="student@example.com",
        first_name="Jane",
        last_name="Smith",
        class_code=Student.Class.SENIOR,
        major_code="CS",
    )


@pytest.fixture
def sample_semester(db):
    return Semester.objects.create(
        semester=Semester.Semester.FALL,
        year=2024,
        assignment_date=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def sample_project(db, sample_sponsor):
    return Project.objects.create(
        name="Test Project",
        description="A test project description",
        sponsor=sample_sponsor,
        status=Project.StatusChoices.PENDING,
        website="https://example.com",
    )


@pytest.mark.django_db
class TestProjectSerializer:
    def test_project_serializer_serializes_status_display_value(self, sample_project):
        serializer = ProjectSerializer(instance=sample_project)

        assert serializer.data["status"] == "Pending"
        assert serializer.data["name"] == "Test Project"

    def test_project_serializer_creates_project_with_default_status(self, sample_sponsor):
        serializer = ProjectSerializer(
            data={
                "name": "Serializer Created Project",
                "description": "Created through serializer",
                        "sponsor": sample_sponsor.id,
                        "website": "https://serializer.example.com",
            }
        )

        assert serializer.is_valid(), serializer.errors
        project = serializer.save()

        assert project.name == "Serializer Created Project"
        assert project.sponsor == sample_sponsor
        assert project.status == Project.StatusChoices.PENDING

    def test_project_serializer_includes_sponsor_availability(self, sample_sponsor):
        availability = "Monday-Friday, 9am-5pm EST"
        serializer = ProjectSerializer(
            data={
                "name": "Project with Availability",
                "sponsor": sample_sponsor.id,
                        "sponsor_availability": availability,
            }
        )

        assert serializer.is_valid(), serializer.errors
        project = serializer.save()

        assert project.sponsor_availability == availability

    def test_project_serializer_serializes_sponsor_availability(self, sample_sponsor):
        project = Project.objects.create(
            name="Project with Availability",
            sponsor=sample_sponsor,
            sponsor_availability="Tuesday and Thursday afternoons",
        )
        serializer = ProjectSerializer(instance=project)

        assert serializer.data["sponsor_availability"] == "Tuesday and Thursday afternoons"
        assert serializer.data["name"] == "Project with Availability"

    def test_project_serializer_sponsor_availability_optional(self, sample_sponsor):
        serializer = ProjectSerializer(
            data={
                "name": "Project without Availability",
                "sponsor": sample_sponsor.id,
            }
        )

        assert serializer.is_valid(), serializer.errors
        project = serializer.save()

        assert project.sponsor_availability is None


@pytest.mark.django_db
class TestSemesterSerializer:
    def test_semester_serializer_serializes_projects_ids(self, sample_semester, sample_project, sample_sponsor):
        second_project = Project.objects.create(
            name="Second Project",
            sponsor=sample_sponsor,
        )
        sample_semester.projects.add(sample_project, second_project)

        serializer = SemesterSerializer(instance=sample_semester)
        serialized_ids = set(serializer.data["projects"])

        assert serialized_ids == {sample_project.id, second_project.id}

    def test_semester_serializer_creates_with_projects(self, sample_project, sample_sponsor):
        second_project = Project.objects.create(
            name="Serializer Semester Project",
            sponsor=sample_sponsor,
        )
        serializer = SemesterSerializer(
            data={
                "semester": Semester.Semester.SPRING,
                "year": 2024,
                "assignment_date": (timezone.now() + timedelta(days=10)).isoformat(),
                "projects": [sample_project.id, second_project.id],
            }
        )

        assert serializer.is_valid(), serializer.errors
        semester = serializer.save()

        assert set(semester.projects.values_list("id", flat=True)) == {
            sample_project.id,
            second_project.id,
        }


@pytest.mark.django_db
class TestAttachmentSerializer:
    def test_attachment_serializer_exposes_download_url(self, sample_project):
        attachment = Attachment(id=1, project=sample_project)
        attachment.file.name = "attachments/project-spec.pdf"

        request = RequestFactory().get("/api/v1/attachments/1/")
        serializer = AttachmentSerializer(instance=attachment, context={"request": request})

        assert serializer.data["url"].endswith("/api/v1/attachments/1/download/")
        assert serializer.data["file"] == "attachments/project-spec.pdf"

    def test_attachment_serializer_creates_link_attachment(self, sample_project):
        serializer = AttachmentSerializer(
            data={
                "project": sample_project.id,
                "link": "https://example.com/spec",
            }
        )

        assert serializer.is_valid(), serializer.errors
        attachment = serializer.save()

        assert attachment.link == "https://example.com/spec"
        assert not attachment.file
        assert serializer.data["url"] == "https://example.com/spec"

    def test_attachment_serializer_rejects_invalid_extension(self, sample_project):
        uploaded_file = SimpleUploadedFile(
            "spec.txt",
            b"plain text",
            content_type="text/plain",
        )

        serializer = AttachmentSerializer(
            data={
                "project": sample_project.id,
                "file": uploaded_file,
            }
        )

        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_attachment_serializer_rejects_oversized_file(self, sample_project):
        uploaded_file = SimpleUploadedFile(
            "spec.pdf",
            b"tiny file",
            content_type="application/pdf",
        )
        uploaded_file.size = MAX_ATTACHMENT_FILE_SIZE + 1

        serializer = AttachmentSerializer(
            data={
                "project": sample_project.id,
                "file": uploaded_file,
            }
        )

        assert not serializer.is_valid()
        assert "file" in serializer.errors


@pytest.mark.django_db
class TestPreferenceSerializer:
    def test_preference_serializer_creates_single_preference(self, sample_student, sample_project):
        serializer = PreferenceSerializer(
            data={
                "student": sample_student.id,
                "project": sample_project.id,
                "rank": Preference.RankChoices.ONE,
            }
        )

        assert serializer.is_valid(), serializer.errors
        preference = serializer.save()

        expected_id = slugify(f"{sample_student.id}-{sample_project.id}")
        assert preference.id == expected_id
        assert preference.rank == Preference.RankChoices.ONE

    def test_preference_serializer_many_create_generates_ids(self, sample_student, sample_sponsor):
        project_one = Project.objects.create(name="Project One", sponsor=sample_sponsor)
        project_two = Project.objects.create(name="Project Two", sponsor=sample_sponsor)

        serializer = PreferenceSerializer(
            many=True,
            data=[
                {
                    "student": sample_student.id,
                    "project": project_one.id,
                    "rank": Preference.RankChoices.ONE,
                },
                {
                    "student": sample_student.id,
                    "project": project_two.id,
                    "rank": Preference.RankChoices.TWO,
                },
            ],
        )

        assert serializer.is_valid(), serializer.errors
        preferences = serializer.save()

        ids = {pref.id for pref in preferences}
        assert ids == {
            slugify(f"{sample_student.id}-{project_one.id}"),
            slugify(f"{sample_student.id}-{project_two.id}"),
        }

    def test_preference_serializer_many_validate_rejects_multiple_students(
            self, sample_student, sample_sponsor
    ):
        second_student = Student.objects.create(
            cwid="87654321",
            email="second.student@example.com",
            first_name="Alex",
            last_name="Taylor",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )
        project_one = Project.objects.create(name="Project One", sponsor=sample_sponsor)
        project_two = Project.objects.create(name="Project Two", sponsor=sample_sponsor)

        serializer = PreferenceSerializer(
            many=True,
            data=[
                {
                    "student": sample_student.id,
                    "project": project_one.id,
                    "rank": Preference.RankChoices.ONE,
                },
                {
                    "student": second_student.id,
                    "project": project_two.id,
                    "rank": Preference.RankChoices.TWO,
                },
            ],
        )

        assert not serializer.is_valid()
        assert "Only 1 student may be updated at a time" in str(serializer.errors)

    def test_preference_serializer_many_validate_rejects_duplicate_projects(
            self, sample_student, sample_project
    ):
        serializer = PreferenceSerializer(
            many=True,
            data=[
                {
                    "student": sample_student.id,
                    "project": sample_project.id,
                    "rank": Preference.RankChoices.ONE,
                },
                {
                    "student": sample_student.id,
                    "project": sample_project.id,
                    "rank": Preference.RankChoices.TWO,
                },
            ],
        )

        assert not serializer.is_valid()
        assert "Only 1 preference per project may be submitted" in str(serializer.errors)

    def test_preference_serializer_many_update_updates_rank(
            self, sample_student, sample_project, sample_sponsor
    ):
        second_project = Project.objects.create(name="Second Update Project", sponsor=sample_sponsor)
        first_preference = Preference.objects.create(
            student=sample_student,
            project=sample_project,
            rank=Preference.RankChoices.ONE,
        )
        second_preference = Preference.objects.create(
            student=sample_student,
            project=second_project,
            rank=Preference.RankChoices.TWO,
        )

        serializer = PreferenceSerializer(
            instance=[first_preference, second_preference],
            many=True,
            data=[
                {
                    "id": first_preference.id,
                    "student": sample_student.id,
                    "project": sample_project.id,
                    "rank": Preference.RankChoices.THREE,
                },
                {
                    "id": second_preference.id,
                    "student": sample_student.id,
                    "project": second_project.id,
                    "rank": Preference.RankChoices.ONE,
                },
            ],
        )

        assert serializer.is_valid(), serializer.errors
        serializer.save()

        first_preference.refresh_from_db()
        second_preference.refresh_from_db()
        assert first_preference.rank == Preference.RankChoices.THREE
        assert second_preference.rank == Preference.RankChoices.ONE


@pytest.mark.django_db
class TestAssignmentSerializer:
    def test_assignment_serializer_creates_assignment(self, sample_student, sample_semester, sample_project):
        serializer = AssignmentSerializer(
            data={
                "student": sample_student.id,
                "semester": sample_semester.id,
                "project": sample_project.id,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assignment = serializer.save()

        expected_id = slugify(f"{sample_student.id}-{sample_semester.id}")
        assert assignment.id == expected_id
        assert assignment.student == sample_student
        assert assignment.semester == sample_semester
        assert assignment.project == sample_project

    def test_assignment_serializer_serializes_fields(self, sample_student, sample_semester, sample_project):
        assignment = Assignment.objects.create(
            student=sample_student,
            semester=sample_semester,
            project=sample_project,
        )
        serializer = AssignmentSerializer(instance=assignment)

        assert serializer.data["id"] == assignment.id
        assert serializer.data["student"] == sample_student.id
        assert serializer.data["semester"] == sample_semester.id
        assert serializer.data["project"] == sample_project.id


@pytest.mark.django_db
class TestFeedbackSerializer:
    def test_feedback_serializer_creates_feedback(self, sample_sponsor, sample_project, sample_semester):
        serializer = FeedbackSerializer(
            data={
                "sponsor": sample_sponsor.id,
                "project": sample_project.id,
                "semester": sample_semester.id,
                "text": "Great progress on the project!",
            }
        )

        assert serializer.is_valid(), serializer.errors
        feedback = serializer.save()

        assert feedback.sponsor == sample_sponsor
        assert feedback.project == sample_project
        assert feedback.semester == sample_semester
        assert feedback.text == "Great progress on the project!"

    def test_feedback_serializer_serializes_fields(self, sample_sponsor, sample_project, sample_semester):
        feedback = Feedback.objects.create(
            sponsor=sample_sponsor,
            project=sample_project,
            semester=sample_semester,
            text="Test feedback text",
        )
        serializer = FeedbackSerializer(instance=feedback)

        assert serializer.data["id"] == feedback.id
        assert serializer.data["sponsor"] == sample_sponsor.id
        assert serializer.data["project"] == sample_project.id
        assert serializer.data["semester"] == sample_semester.id
        assert serializer.data["text"] == "Test feedback text"

    def test_feedback_serializer_includes_timestamps(self, sample_sponsor, sample_project, sample_semester):
        feedback = Feedback.objects.create(
            sponsor=sample_sponsor,
            project=sample_project,
            semester=sample_semester,
            text="Test feedback",
        )
        serializer = FeedbackSerializer(instance=feedback)

        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data
        assert serializer.data["created_at"] is not None
        assert serializer.data["updated_at"] is not None

    def test_feedback_serializer_long_text(self, sample_sponsor, sample_project, sample_semester):
        long_text = "This is feedback. " * 100
        serializer = FeedbackSerializer(
            data={
                "sponsor": sample_sponsor.id,
                "project": sample_project.id,
                "semester": sample_semester.id,
                "text": long_text,
            }
        )

        assert serializer.is_valid(), serializer.errors
        feedback = serializer.save()

        assert feedback.text.strip() == long_text.strip()
        assert len(feedback.text) > 1000

    def test_feedback_serializer_many_create(self, sample_sponsor, sample_project, sample_semester):
        second_semester = Semester.objects.create(
            semester=Semester.Semester.SPRING,
            year=2024,
            assignment_date=timezone.now() + timedelta(days=7),
        )
        serializer = FeedbackSerializer(
            many=True,
            data=[
                {
                    "sponsor": sample_sponsor.id,
                    "project": sample_project.id,
                    "semester": sample_semester.id,
                    "text": "Fall semester feedback",
                },
                {
                    "sponsor": sample_sponsor.id,
                    "project": sample_project.id,
                    "semester": second_semester.id,
                    "text": "Spring semester feedback",
                },
            ],
        )

        assert serializer.is_valid(), serializer.errors
        feedbacks = serializer.save()

        assert len(feedbacks) == 2
        assert feedbacks[0].text == "Fall semester feedback"
        assert feedbacks[1].text == "Spring semester feedback"

    def test_feedback_serializer_validates_required_fields(self):
        serializer = FeedbackSerializer(data={})
        assert not serializer.is_valid()
        # Should have errors for required fields
        assert "sponsor" in serializer.errors or len(serializer.errors) > 0
