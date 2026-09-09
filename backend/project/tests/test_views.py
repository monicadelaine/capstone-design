from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.test import APIClient

from project.models import Assignment, Feedback, Preference, Project, Semester
from user.models import Sponsor, Student


@pytest.fixture
def api_client(db):
    """Create an authenticated API client for testing."""
    client = APIClient()
    # Create a test user for authentication
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    # Force authenticate the client with the test user
    client.force_authenticate(user=user)
    return client


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
def second_sponsor(db):
    return Sponsor.objects.create(
        email="second.sponsor@example.com",
        first_name="Sarah",
        last_name="Conor",
        organization="Skynet Labs",
        phone_number="(555) 555-1234",
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


@pytest.fixture
def sample_preference(db, sample_student, sample_project):
    return Preference.objects.create(
        student=sample_student,
        project=sample_project,
        rank=Preference.RankChoices.ONE,
    )


@pytest.fixture
def sample_assignment(db, sample_student, sample_semester, sample_project):
    return Assignment.objects.create(
        student=sample_student,
        semester=sample_semester,
        project=sample_project,
    )


@pytest.fixture
def sample_feedback(db, sample_sponsor, sample_project, sample_semester):
    return Feedback.objects.create(
        sponsor=sample_sponsor,
        project=sample_project,
        semester=sample_semester,
        text="Great work on this project!",
    )


@pytest.mark.django_db
class TestProjectViewSet:
    def test_list_projects(self, api_client, sample_project):
        url = reverse("project:project-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == sample_project.id

    def test_create_project(self, api_client, sample_sponsor):
        url = reverse("project:project-list")
        payload = {
            "name": "Created by API",
            "description": "From viewset",
            "sponsor": sample_sponsor.id,
            "website": "https://created.example.com",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Project.objects.filter(name="Created by API").exists()

    def test_filter_projects_by_sponsor(self, api_client, sample_sponsor, second_sponsor):
        matching = Project.objects.create(name="Matching", sponsor=sample_sponsor)
        Project.objects.create(name="Not Matching", sponsor=second_sponsor)

        url = reverse("project:project-list")
        response = api_client.get(url, {"sponsor": sample_sponsor.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == matching.id


@pytest.mark.django_db
class TestPreferenceAPIView:
    def test_get_preference_list(self, api_client, sample_preference):
        url = reverse("project:preference-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == sample_preference.id

    def test_get_preference_detail(self, api_client, sample_preference):
        url = reverse("project:preference-detail", kwargs={"pk": sample_preference.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == sample_preference.id

    def test_post_single_preference(self, api_client, sample_student, sample_project):
        url = reverse("project:preference-list")
        payload = {
            "student": sample_student.id,
            "project": sample_project.id,
            "rank": Preference.RankChoices.ONE,
        }

        response = api_client.post(url, payload, format="json")
        expected_id = slugify(f"{sample_student.id}-{sample_project.id}")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == expected_id
        assert Preference.objects.filter(pk=expected_id).exists()

    def test_post_multiple_preferences(self, api_client, sample_student, sample_sponsor):
        first_project = Project.objects.create(name="Project One", sponsor=sample_sponsor)
        second_project = Project.objects.create(name="Project Two", sponsor=sample_sponsor)
        url = reverse("project:preference-list")
        payload = [
            {
                "student": sample_student.id,
                "project": first_project.id,
                "rank": Preference.RankChoices.ONE,
            },
            {
                "student": sample_student.id,
                "project": second_project.id,
                "rank": Preference.RankChoices.TWO,
            },
        ]

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 2
        assert Preference.objects.count() == 2

    def test_patch_preference_by_pk(self, api_client, sample_preference):
        url = reverse("project:preference-detail", kwargs={"pk": sample_preference.id})
        response = api_client.patch(url, {"rank": Preference.RankChoices.THREE}, format="json")

        assert response.status_code == status.HTTP_200_OK
        sample_preference.refresh_from_db()
        assert sample_preference.rank == Preference.RankChoices.THREE

    def test_patch_preference_constructs_pk_from_student_and_project(
            self, api_client, sample_preference, sample_student, sample_project
    ):
        url = reverse("project:preference-list")
        payload = {
            "student": sample_student.id,
            "project": sample_project.id,
            "rank": Preference.RankChoices.TWO,
        }

        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        sample_preference.refresh_from_db()
        assert sample_preference.rank == Preference.RankChoices.TWO

    def test_patch_preference_missing_identifying_fields_returns_400(self, api_client):
        url = reverse("project:preference-list")
        response = api_client.patch(url, {"rank": Preference.RankChoices.TWO}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_delete_preference_detail(self, api_client, sample_preference):
        url = reverse("project:preference-detail", kwargs={"pk": sample_preference.id})
        response = api_client.delete(url)

        # A 204 response would be preferred here, but because DRF returns the browsable API a 204 gets
        # converted to a 200 because the HTML form is appended, and a 204 does not allow content
        assert response.status_code == status.HTTP_200_OK
        assert not Preference.objects.filter(pk=sample_preference.id).exists()

    def test_delete_preference_without_pk_returns_400(self, api_client):
        url = reverse("project:preference-list")
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data


@pytest.mark.django_db
class TestAssignmentViewSet:
    def test_list_assignments(self, api_client, sample_assignment):
        url = reverse("project:assignment-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == sample_assignment.id

    def test_create_assignment(self, api_client, sample_student, sample_semester, sample_project):
        url = reverse("project:assignment-list")
        payload = {
            "student": sample_student.id,
            "semester": sample_semester.id,
            "project": sample_project.id,
        }

        response = api_client.post(url, payload, format="json")
        expected_id = slugify(f"{sample_student.id}-{sample_semester.id}")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] == expected_id
        assert Assignment.objects.filter(pk=expected_id).exists()

    def test_filter_assignments_by_project(self, api_client, sample_assignment, sample_sponsor):
        matching_student = Student.objects.create(
            cwid="87654321",
            email="matching.student@example.com",
            first_name="Match",
            last_name="Student",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )
        non_matching_project = Project.objects.create(name="Other Project", sponsor=sample_sponsor)
        non_matching_student = Student.objects.create(
            cwid="87654322",
            email="non.matching.student@example.com",
            first_name="Non",
            last_name="Matching",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )

        matching_assignment = Assignment.objects.create(
            student=matching_student,
            semester=sample_assignment.semester,
            project=sample_assignment.project,
        )
        Assignment.objects.create(
            student=non_matching_student,
            semester=sample_assignment.semester,
            project=non_matching_project,
        )

        url = reverse("project:assignment-list")
        response = api_client.get(url, {"project": sample_assignment.project.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        returned_ids = {item["id"] for item in response.data}
        assert returned_ids == {sample_assignment.id, matching_assignment.id}

    def test_filter_assignments_by_semester(self, api_client, sample_assignment, sample_sponsor):
        matching_student = Student.objects.create(
            cwid="87654323",
            email="semester.matching.student@example.com",
            first_name="Semester",
            last_name="Match",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )
        other_semester = Semester.objects.create(
            semester=Semester.Semester.SPRING,
            year=2025,
            assignment_date=timezone.now() + timedelta(days=30),
        )
        non_matching_student = Student.objects.create(
            cwid="87654324",
            email="semester.non.matching.student@example.com",
            first_name="Semester",
            last_name="NonMatch",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )

        matching_assignment = Assignment.objects.create(
            student=matching_student,
            semester=sample_assignment.semester,
            project=sample_assignment.project,
        )
        Assignment.objects.create(
            student=non_matching_student,
            semester=other_semester,
            project=sample_assignment.project,
        )

        url = reverse("project:assignment-list")
        response = api_client.get(url, {"semester": sample_assignment.semester.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        returned_ids = {item["id"] for item in response.data}
        assert returned_ids == {sample_assignment.id, matching_assignment.id}

    def test_filter_assignments_by_project_and_semester(self, api_client, sample_assignment, sample_sponsor):
        target_project = sample_assignment.project
        target_semester = sample_assignment.semester

        matching_student = Student.objects.create(
            cwid="87654325",
            email="combo.matching.student@example.com",
            first_name="Combo",
            last_name="Match",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )
        other_project = Project.objects.create(name="Combo Other Project", sponsor=sample_sponsor)
        other_semester = Semester.objects.create(
            semester=Semester.Semester.SPRING,
            year=2026,
            assignment_date=timezone.now() + timedelta(days=45),
        )

        matching_assignment = Assignment.objects.create(
            student=matching_student,
            semester=target_semester,
            project=target_project,
        )

        project_only_student = Student.objects.create(
            cwid="87654326",
            email="project.only.student@example.com",
            first_name="Project",
            last_name="Only",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )
        Assignment.objects.create(
            student=project_only_student,
            semester=other_semester,
            project=target_project,
        )

        semester_only_student = Student.objects.create(
            cwid="87654327",
            email="semester.only.student@example.com",
            first_name="Semester",
            last_name="Only",
            class_code=Student.Class.SENIOR,
            major_code="CS",
        )
        Assignment.objects.create(
            student=semester_only_student,
            semester=target_semester,
            project=other_project,
        )

        url = reverse("project:assignment-list")
        response = api_client.get(
            url,
            {"project": target_project.id, "semester": target_semester.id},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        returned_ids = {item["id"] for item in response.data}
        assert returned_ids == {sample_assignment.id, matching_assignment.id}


@pytest.mark.django_db
class TestFeedbackViewSet:
    def test_list_feedback(self, api_client, sample_feedback):
        url = reverse("project:feedback-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == sample_feedback.id

    def test_create_feedback(self, api_client, sample_sponsor, sample_project, sample_semester):
        url = reverse("project:feedback-list")
        payload = {
            "sponsor": sample_sponsor.id,
            "project": sample_project.id,
            "semester": sample_semester.id,
            "text": "Excellent progress on the design.",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Feedback.objects.filter(text="Excellent progress on the design.").exists()
        assert response.data["text"] == "Excellent progress on the design."

    def test_retrieve_feedback(self, api_client, sample_feedback):
        url = reverse("project:feedback-detail", kwargs={"pk": sample_feedback.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == sample_feedback.id
        assert response.data["text"] == "Great work on this project!"

    def test_update_feedback(self, api_client, sample_feedback):
        url = reverse("project:feedback-detail", kwargs={"pk": sample_feedback.id})
        payload = {"text": "Updated feedback text"}

        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        sample_feedback.refresh_from_db()
        assert sample_feedback.text == "Updated feedback text"

    def test_delete_feedback(self, api_client, sample_feedback):
        feedback_id = sample_feedback.id
        url = reverse("project:feedback-detail", kwargs={"pk": feedback_id})
        response = api_client.delete(url)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        assert not Feedback.objects.filter(pk=feedback_id).exists()

    def test_create_multiple_feedback_for_same_project(self, api_client, sample_sponsor, sample_project, sample_semester):
        url = reverse("project:feedback-list")
        payload1 = {
            "sponsor": sample_sponsor.id,
            "project": sample_project.id,
            "semester": sample_semester.id,
            "text": "First feedback",
        }

        response1 = api_client.post(url, payload1, format="json")
        assert response1.status_code == status.HTTP_201_CREATED

        second_sponsor = Sponsor.objects.create(
            email="second.feedback.sponsor@example.com",
            first_name="Bob",
            last_name="Builder",
            organization="BuildCorp",
            phone_number="(555) 123-4567",
        )
        payload2 = {
            "sponsor": second_sponsor.id,
            "project": sample_project.id,
            "semester": sample_semester.id,
            "text": "Second feedback",
        }

        response2 = api_client.post(url, payload2, format="json")
        assert response2.status_code == status.HTTP_201_CREATED

        # Verify both feedbacks exist
        assert Feedback.objects.filter(project=sample_project).count() == 2

    def test_feedback_preserves_sponsor_relation(self, api_client, sample_feedback, sample_sponsor):
        url = reverse("project:feedback-detail", kwargs={"pk": sample_feedback.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["sponsor"] == sample_sponsor.id

    def test_feedback_preserves_project_relation(self, api_client, sample_feedback, sample_project):
        url = reverse("project:feedback-detail", kwargs={"pk": sample_feedback.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["project"] == sample_project.id

    def test_feedback_preserves_semester_relation(self, api_client, sample_feedback, sample_semester):
        url = reverse("project:feedback-detail", kwargs={"pk": sample_feedback.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["semester"] == sample_semester.id
