import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from project.admin import PreferenceAdmin, ProjectAdmin
from project.models import Assignment, Preference, Project, Semester
from user.models import Sponsor, Student


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
def sample_student(db):
    return Student.objects.create(
        cwid="12345678",
        first_name="Bob",
        last_name="Smith",
        email="bob@example.com",
        class_code=Student.Class.SENIOR,
        major_code="CS",
    )


@pytest.fixture
def sample_project(db, sample_sponsor):
    return Project.objects.create(
        name="Test Project",
        sponsor=sample_sponsor,
        status=Project.StatusChoices.PENDING,
    )


@pytest.fixture
def matching_semester(db):
    return Semester.objects.create(
        semester=Semester.get_semester_by_date(timezone.now()),
        year=timezone.now().year,
        assignment_date=timezone.now(),
    )


@pytest.mark.django_db
class TestProjectAdminActions:
    def test_change_project_status_action_updates_projects(self, rf, admin_user, sample_project):
        admin_instance = ProjectAdmin(Project, admin.site)
        request = rf.post("/")
        request.user = admin_user
        messages = []
        admin_instance.message_user = lambda request, message, level=None: messages.append((message, level))

        queryset = Project.objects.filter(pk=sample_project.pk)
        admin_instance.change_project_status_action.__wrapped__(
            admin_instance,
            request,
            queryset,
            {"status": Project.StatusChoices.COMPLETE},
        )

        sample_project.refresh_from_db()
        assert sample_project.status == Project.StatusChoices.COMPLETE
        assert messages == [("Status changed to CMPL for 1 projects.", None)]

    def test_assign_project_to_semester_adds_projects(self, rf, admin_user, sample_project, matching_semester):
        admin_instance = ProjectAdmin(Project, admin.site)
        request = rf.post("/")
        request.user = admin_user
        messages = []
        admin_instance.message_user = lambda request, message, level=None: messages.append((message, level))

        queryset = Project.objects.filter(pk=sample_project.pk)
        admin_instance.assign_project_to_semester.__wrapped__(
            admin_instance,
            request,
            queryset,
            {"semester": [matching_semester]},
        )

        matching_semester.refresh_from_db()
        assert list(matching_semester.projects.values_list("id", flat=True)) == [sample_project.id]
        assert messages == [("Assigned 1 projects to 1 semesters.", None)]

    def test_remove_project_from_semester_removes_projects(self, rf, admin_user, sample_project, matching_semester):
        matching_semester.projects.add(sample_project)
        admin_instance = ProjectAdmin(Project, admin.site)
        request = rf.get("/", {"semester": matching_semester.id})
        request.user = admin_user
        messages = []
        admin_instance.message_user = lambda request, message, level=None: messages.append((message, level))

        queryset = Project.objects.filter(pk=sample_project.pk)
        admin_instance.remove_project_from_semester.__wrapped__(admin_instance, request, queryset, {})

        matching_semester.refresh_from_db()
        assert matching_semester.projects.count() == 0
        assert messages == [(f"Removed 1 projects from {matching_semester}.", None)]

    def test_remove_project_from_semester_without_filter_reports_error(self, rf, admin_user, sample_project):
        admin_instance = ProjectAdmin(Project, admin.site)
        request = rf.get("/")
        request.user = admin_user
        messages = []
        admin_instance.message_user = lambda request, message, level=None: messages.append((message, level))

        queryset = Project.objects.filter(pk=sample_project.pk)
        admin_instance.remove_project_from_semester.__wrapped__(admin_instance, request, queryset, {})

        assert messages == [("Filter the projects by a semester first", "error")]


@pytest.mark.django_db
class TestPreferenceAdminAction:
    def test_assign_to_project_creates_assignments(self, rf, admin_user, sample_student, sample_project, sample_sponsor, matching_semester):
        other_project = Project.objects.create(name="Other Project", sponsor=sample_sponsor)
        preference = Preference.objects.create(
            student=sample_student,
            project=other_project,
            rank=Preference.RankChoices.ONE,
        )
        admin_instance = PreferenceAdmin(Preference, admin.site)
        request = rf.post("/")
        request.user = admin_user
        messages = []
        admin_instance.message_user = lambda request, message, level=None: messages.append((message, level))

        queryset = Preference.objects.filter(pk=preference.pk)
        admin_instance.assign_to_project.__wrapped__(admin_instance, request, queryset, {"project": sample_project})

        assert Assignment.objects.filter(
            student=sample_student, semester=matching_semester, project=sample_project).exists()
        assert len(messages) == 1
        assert messages[0][0].startswith("Assigned selected students to Test Project.")

    def test_assign_to_project_rejects_duplicate_students(self, rf, admin_user, sample_student, sample_sponsor, matching_semester):
        first_project = Project.objects.create(name="First Project", sponsor=sample_sponsor)
        second_project = Project.objects.create(name="Second Project", sponsor=sample_sponsor)
        first_preference = Preference.objects.create(
            student=sample_student,
            project=first_project,
            rank=Preference.RankChoices.ONE,
        )
        second_preference = Preference.objects.create(
            student=sample_student,
            project=second_project,
            rank=Preference.RankChoices.TWO,
        )
        admin_instance = PreferenceAdmin(Preference, admin.site)
        request = rf.post("/")
        request.user = admin_user
        messages = []
        admin_instance.message_user = lambda request, message, level=None: messages.append((message, level))

        queryset = Preference.objects.filter(pk__in=[first_preference.pk, second_preference.pk]).order_by("pk")
        admin_instance.assign_to_project.__wrapped__(admin_instance, request, queryset, {"project": first_project})

        assert messages == [(
            "Select each student only once before assigning them to a project.",
            "error",
        )]
        assert Assignment.objects.filter(
            student=sample_student, semester=matching_semester, project=first_project).exists()
