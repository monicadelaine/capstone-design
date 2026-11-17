import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from project.admin import ProjectAdmin
from project.models import Assignment, Project, Semester
from project.review import ReviewError, approve_project, pending_projects, reject_project
from project.tests.test_views import make_client
from user.models import Sponsor, Student


@pytest.fixture
def semester(db):
    """The semester the project list shows: the one for today's date."""
    now = timezone.now()
    return Semester.objects.create(semester=Semester.get_semester_by_date(now), year=now.year, assignment_date=now)


@pytest.fixture
def other_semester(db, semester):
    return Semester.objects.create(semester='Summer', year=semester.year - 1, assignment_date=timezone.now())


@pytest.fixture
def sponsor(db):
    return Sponsor.objects.create(first_name='Ada', last_name='Lovelace', email='ada@example.com', organization='Engines')


@pytest.fixture
def student(db):
    return Student.objects.create(cwid='12345678', first_name='Sam', last_name='Student', email='sam@example.com')


@pytest.fixture
def project(db, sponsor):
    return Project.objects.create(name='Route Planner', description='Plan accessible routes.', sponsor=sponsor)


@pytest.fixture
def admin_api(db):
    return make_client('admin@example.com', ['admin'])


@pytest.fixture
def sponsor_api(db, sponsor):
    return make_client(sponsor.email, ['sponsor'])


@pytest.fixture
def other_sponsor_api(db):
    Sponsor.objects.create(first_name='Grace', last_name='Hopper', email='grace@example.com')
    return make_client('grace@example.com', ['sponsor'])


@pytest.fixture
def student_api(db, student):
    return make_client(student.email, ['student'])


def listed(client):
    """Names in the project list a client sees (the current semester's projects)."""
    return [p['name'] for p in client.get(reverse('project:project-list')).data]


@pytest.mark.django_db
class TestReviewService:
    def test_pending_is_unreviewed_projects_oldest_first(self, sponsor, semester):
        first = Project.objects.create(name='First', sponsor=sponsor)
        second = Project.objects.create(name='Second', sponsor=sponsor)
        approved = Project.objects.create(name='Approved', sponsor=sponsor)
        semester.projects.add(approved)
        Project.objects.create(name='Rejected', sponsor=sponsor, status=Project.StatusChoices.CANCELLED)

        assert list(pending_projects()) == [first, second]

    def test_approve_defaults_to_the_current_semester(self, project, semester, other_semester):
        assert approve_project(project) == semester
        assert list(semester.projects.all()) == [project]
        assert other_semester.projects.count() == 0

    def test_approve_into_a_chosen_semester(self, project, semester, other_semester):
        approve_project(project, other_semester)
        assert list(other_semester.projects.all()) == [project]
        assert semester.projects.count() == 0

    def test_approve_without_a_current_semester_explains_why(self, project):
        with pytest.raises(ReviewError, match='no semester for the current date'):
            approve_project(project)

    def test_reject_cancels_and_removes_from_every_semester(self, project, semester, other_semester):
        semester.projects.add(project)
        other_semester.projects.add(project)

        reject_project(project)

        project.refresh_from_db()
        assert project.status == Project.StatusChoices.CANCELLED
        assert semester.projects.count() == 0 and other_semester.projects.count() == 0

    def test_approving_a_rejected_project_restores_it(self, project, semester):
        reject_project(project)

        approve_project(project)

        project.refresh_from_db()
        assert project.status == Project.StatusChoices.PENDING
        assert list(semester.projects.all()) == [project]

    def test_reject_refuses_a_project_with_students_assigned(self, project, semester, student):
        semester.projects.add(project)
        Assignment.objects.create(student=student, semester=semester, project=project)

        with pytest.raises(ReviewError, match='already has students assigned'):
            reject_project(project)

        project.refresh_from_db()
        assert project.status == Project.StatusChoices.PENDING
        assert list(semester.projects.all()) == [project]


@pytest.mark.django_db
class TestReviewApi:
    def test_admin_sees_pending_projects_with_sponsor_and_description(self, admin_api, project):
        response = admin_api.get(reverse('project:project-pending'))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        row = response.data[0]
        assert row['name'] == 'Route Planner'
        assert row['description'] == 'Plan accessible routes.'
        assert row['status'] == 'Pending'
        assert row['sponsor'] == {'id': project.sponsor_id, 'name': 'Ada Lovelace',
                                  'organization': 'Engines', 'email': 'ada@example.com'}
        assert row['semesters'] == []

    def test_approve_makes_the_project_visible_to_students(self, admin_api, student_api, project, semester):
        assert listed(student_api) == []

        response = admin_api.post(reverse('project:project-approve', args=[project.id]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['semesters'] == [{'id': semester.id, 'name': str(semester)}]
        assert listed(student_api) == ['Route Planner']
        assert admin_api.get(reverse('project:project-pending')).data == []

    def test_approve_into_a_named_semester(self, admin_api, project, semester, other_semester):
        response = admin_api.post(reverse('project:project-approve', args=[project.id]),
                                  {'semester': other_semester.id}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert list(other_semester.projects.all()) == [project]
        assert semester.projects.count() == 0

    def test_approve_with_an_unknown_semester_is_a_400(self, admin_api, project, semester):
        response = admin_api.post(reverse('project:project-approve', args=[project.id]),
                                  {'semester': 99999}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {'error': 'That semester does not exist.'}
        assert semester.projects.count() == 0

    def test_approve_without_a_current_semester_is_a_400(self, admin_api, project):
        response = admin_api.post(reverse('project:project-approve', args=[project.id]))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'no semester for the current date' in response.data['error']

    def test_reject_hides_the_project_from_students(self, admin_api, student_api, project, semester):
        semester.projects.add(project)
        assert listed(student_api) == ['Route Planner']

        response = admin_api.post(reverse('project:project-reject', args=[project.id]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'Cancelled'
        assert listed(student_api) == []
        detail = student_api.get(reverse('project:project-detail', args=[project.id]))
        assert detail.status_code == status.HTTP_404_NOT_FOUND

    def test_a_cancelled_project_left_on_a_semester_is_still_hidden(self, student_api, admin_api, project, semester):
        # Status changed by hand in Django admin, without the reject action.
        semester.projects.add(project)
        Project.objects.filter(pk=project.pk).update(status=Project.StatusChoices.CANCELLED)

        assert listed(student_api) == []
        assert listed(admin_api) == ['Route Planner']

    def test_rejected_project_stays_visible_to_its_sponsor_only(self, admin_api, sponsor_api, other_sponsor_api, project):
        admin_api.post(reverse('project:project-reject', args=[project.id]))
        detail = reverse('project:project-detail', args=[project.id])

        assert sponsor_api.get(detail).status_code == status.HTTP_200_OK
        assert sponsor_api.get(detail).data['status'] == 'Cancelled'
        assert other_sponsor_api.get(detail).status_code == status.HTTP_404_NOT_FOUND

    def test_reject_with_students_assigned_is_a_400(self, admin_api, project, semester, student):
        semester.projects.add(project)
        Assignment.objects.create(student=student, semester=semester, project=project)

        response = admin_api.post(reverse('project:project-reject', args=[project.id]))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already has students assigned' in response.data['error']

    @pytest.mark.parametrize('client_fixture', ['sponsor_api', 'student_api'])
    def test_sponsors_and_students_cannot_review(self, request, client_fixture, project, semester):
        client = request.getfixturevalue(client_fixture)

        assert client.get(reverse('project:project-pending')).status_code == status.HTTP_403_FORBIDDEN
        assert client.post(reverse('project:project-approve', args=[project.id])).status_code == status.HTTP_403_FORBIDDEN
        assert client.post(reverse('project:project-reject', args=[project.id])).status_code == status.HTTP_403_FORBIDDEN

        project.refresh_from_db()
        assert project.status == Project.StatusChoices.PENDING
        assert semester.projects.count() == 0

    def test_review_needs_a_login(self, db, project):
        from rest_framework.test import APIClient
        response = APIClient().get(reverse('project:project-pending'))
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_owning_sponsor_cannot_change_status_by_editing(self, sponsor_api, project):
        detail = reverse('project:project-detail', args=[project.id])

        patch = sponsor_api.patch(detail, {'status': 'IP'}, format='json')
        put = sponsor_api.put(detail, {'name': project.name, 'sponsor': project.sponsor_id, 'status': 'CMPL'}, format='json')

        assert patch.status_code == status.HTTP_200_OK and put.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.status == Project.StatusChoices.PENDING

    def test_student_cannot_change_status(self, student_api, project, semester):
        semester.projects.add(project)

        response = student_api.patch(reverse('project:project-detail', args=[project.id]), {'status': 'CNCL'}, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        project.refresh_from_db()
        assert project.status == Project.StatusChoices.PENDING


@pytest.mark.django_db
class TestProjectAdminReview:
    @pytest.fixture
    def run(self):
        """Call a ProjectAdmin action the way the admin does, collecting its messages."""
        def run(action, queryset, data):
            admin_instance = ProjectAdmin(Project, admin.site)
            request = RequestFactory().post('/')
            request.user = User(username='admin', is_staff=True, is_superuser=True)
            messages = []
            admin_instance.message_user = lambda request, message, level=None: messages.append((message, level))
            getattr(admin_instance, action).__wrapped__(admin_instance, request, queryset, data)
            return messages
        return run

    def test_approve_action_adds_projects_to_the_semester(self, run, project, semester):
        messages = run('approve_projects', Project.objects.filter(pk=project.pk), {'semester': semester})

        assert list(semester.projects.all()) == [project]
        assert messages == [(f'Approved 1 project(s) for {semester}.', None)]

    def test_reject_action_cancels_projects(self, run, project, semester):
        semester.projects.add(project)

        messages = run('reject_projects', Project.objects.filter(pk=project.pk), {})

        project.refresh_from_db()
        assert project.status == Project.StatusChoices.CANCELLED
        assert semester.projects.count() == 0
        assert messages == [('Rejected 1 project(s).', None)]

    def test_reject_action_reports_projects_it_cannot_reject(self, run, project, sponsor, semester, student):
        free = Project.objects.create(name='Free', sponsor=sponsor)
        semester.projects.add(project)
        Assignment.objects.create(student=student, semester=semester, project=project)

        messages = run('reject_projects', Project.objects.filter(pk__in=[project.pk, free.pk]).order_by('name'), {})

        assert messages == [
            ('Route Planner already has students assigned. Reassign them before rejecting it.', 'error'),
            ('Rejected 1 project(s).', None),
        ]
        project.refresh_from_db()
        assert project.status == Project.StatusChoices.PENDING

    def test_waiting_for_review_filter(self, project, sponsor, semester):
        approved = Project.objects.create(name='Approved', sponsor=sponsor)
        semester.projects.add(approved)
        admin_instance = ProjectAdmin(Project, admin.site)

        review_filter = ProjectAdmin.ReviewFilter(None, {'review': ['pending']}, Project, admin_instance)

        assert list(review_filter.queryset(None, Project.objects.all())) == [project]

    def test_approve_through_the_admin_form(self, admin_client, project, semester):
        url = reverse('admin:project_project_changelist')
        select = {'action': 'approve_projects', 'index': 0, '_selected_action': [project.id]}

        form_page = admin_client.post(url, {**select, 'submitted_from_changelist_view': '1'})
        assert form_page.status_code == 200
        assert form_page.context['form'].fields['semester'].initial == semester

        response = admin_client.post(url, {**select, 'semester': semester.id})

        assert response.status_code == 302
        assert list(semester.projects.all()) == [project]
