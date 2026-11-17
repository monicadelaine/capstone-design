import pytest
from django.contrib.auth.models import Permission, User
from django.core import mail
from django.core import signing
from django.urls import reverse
from django.utils import timezone

from project.assignment import (
    TOKEN_SALT, ProposalError, approve, approve_with_changes, edit, pending_moves, propose, solve,
)
from project.models import Assignment, Preference, Project, Semester
from user.models import Sponsor, Student


class TestSolve:
    def test_known_optimum(self):
        # Two students want project 0 first; with teams of 2 everyone gets a first or ranked choice.
        prefs = {0: {0: 1, 1: 2}, 1: {0: 1, 1: 2}, 2: {1: 1}, 3: {1: 1}}
        result, status = solve(prefs, [0, 1], capacity=2)
        assert status == 'OPTIMAL'
        assert result == {0: 0, 1: 0, 2: 1, 3: 1}

    def test_projects_beyond_the_teams_needed_stay_empty(self):
        prefs = {0: {'a': 1}, 1: {'a': 1}, 2: {'b': 1}, 3: {'b': 1}}
        result, _ = solve(prefs, ['a', 'b', 'c'], capacity=2)
        assert sorted(result.values()) == ['a', 'a', 'b', 'b']

    def test_every_used_project_gets_a_full_team_by_default(self):
        prefs = {s: {'a': 1} for s in range(4)}
        result, _ = solve(prefs, ['a', 'b'], capacity=2)
        assert sorted(result.values()) == ['a', 'a', 'b', 'b']

    def test_uneven_cohort_needs_a_lower_minimum(self):
        prefs = {s: {'a': 1, 'b': 2} for s in range(5)}
        with pytest.raises(ProposalError, match='teams of 4'):
            solve(prefs, ['a', 'b'], capacity=4)
        result, _ = solve(prefs, ['a', 'b'], capacity=4, min_size=1)
        assert sorted(result.values()).count('a') == 4

    def test_minimum_above_team_size_is_rejected(self):
        with pytest.raises(ProposalError, match='Minimum team size'):
            solve({0: {}}, ['a'], capacity=2, min_size=3)


@pytest.fixture
def semester(db):
    now = timezone.now()
    return Semester.objects.create(semester=Semester.get_semester_by_date(now), year=now.year, assignment_date=now)


@pytest.fixture
def sponsor(db):
    return Sponsor.objects.create(first_name='Ada', last_name='Lovelace', email='ada@example.com', organization='Engines')


def make_projects(semester, sponsor, names):
    projects = [Project.objects.create(name=name, sponsor=sponsor) for name in names]
    semester.projects.add(*projects)
    return projects


def make_students(count):
    return [
        Student.objects.create(cwid=f'{10000000 + i}', first_name=f'S{i}', last_name='Test', email=f's{i}@example.com')
        for i in range(count)
    ]


def rank(student, *projects):
    for i, project in enumerate(projects, start=1):
        Preference.objects.create(student=student, project=project, rank=i)


@pytest.mark.django_db
class TestPropose:
    def test_builds_teams_from_preferences_and_saves_nothing(self, semester, sponsor):
        alpha, beta, gamma = make_projects(semester, sponsor, ['Alpha', 'Beta', 'Gamma'])
        students = make_students(4)
        for s in students[:2]:
            rank(s, alpha, beta)
        for s in students[2:]:
            rank(s, beta, alpha)

        proposal = propose(semester, capacity=2)

        assert [team.project for team in proposal.teams] == [alpha, beta]
        assert {s for s, _ in proposal.teams[0].members} == set(students[:2])
        assert proposal.unused_projects == [gamma]
        assert proposal.rank_counts == {'first': 4, 'second': 0, 'third': 0, 'unranked': 0}
        assert Assignment.objects.count() == 0

    def test_skips_cancelled_projects(self, semester, sponsor):
        alpha, cancelled = make_projects(semester, sponsor, ['Alpha', 'Cancelled'])
        cancelled.status = Project.StatusChoices.CANCELLED
        cancelled.save()
        student, = make_students(1)
        rank(student, cancelled, alpha)

        proposal = propose(semester, capacity=1)

        assert proposal.teams[0].project == alpha
        assert proposal.teams[0].members == [(student, 2)]

    def test_semester_without_projects(self, semester):
        with pytest.raises(ProposalError, match='has no projects'):
            propose(semester)

    def test_semester_without_preferences(self, semester, sponsor):
        make_projects(semester, sponsor, ['Alpha'])
        with pytest.raises(ProposalError, match='No student has submitted preferences'):
            propose(semester)

    def test_not_enough_seats(self, semester, sponsor):
        alpha, = make_projects(semester, sponsor, ['Alpha'])
        for s in make_students(3):
            rank(s, alpha)
        with pytest.raises(ProposalError, match='3 students but only 2 seats'):
            propose(semester, capacity=2)


@pytest.mark.django_db
class TestApprove:
    @pytest.fixture
    def proposal(self, semester, sponsor):
        alpha, beta = make_projects(semester, sponsor, ['Alpha', 'Beta'])
        students = make_students(2)
        rank(students[0], alpha, beta)
        rank(students[1], beta, alpha)
        return propose(semester, capacity=1)

    def test_creates_assignments(self, proposal, semester):
        assert approve(proposal.token()) == (semester, 2, 0)
        assert set(Assignment.objects.values_list('student__first_name', 'project__name')) == {
            ('S0', 'Alpha'), ('S1', 'Beta')}

    def test_replaces_existing_assignment_for_the_semester(self, proposal, semester):
        student = proposal.teams[0].members[0][0]
        other = proposal.teams[1].project
        Assignment.objects.create(student=student, semester=semester, project=other)

        assert approve(proposal.token()) == (semester, 1, 1)
        assert Assignment.objects.get(student=student, semester=semester).project == proposal.teams[0].project

    def test_reports_the_students_whose_assignment_changed(self, proposal, semester):
        moved, same = proposal.teams[0].members[0][0], proposal.teams[1].members[0][0]
        Assignment.objects.create(student=moved, semester=semester, project=proposal.teams[1].project)
        Assignment.objects.create(student=same, semester=semester, project=proposal.teams[1].project)

        _, created, updated, changed = approve_with_changes(proposal.token())

        assert (created, updated) == (0, 2)
        assert changed == [moved.id]

    def test_rejects_a_tampered_token(self, proposal):
        with pytest.raises(ProposalError, match='could not be verified'):
            approve(proposal.token() + 'x')
        assert Assignment.objects.count() == 0

    def test_rejects_an_expired_token(self, proposal, monkeypatch):
        token = proposal.token()
        monkeypatch.setattr('project.assignment.TOKEN_MAX_AGE', -1)
        with pytest.raises(ProposalError, match='more than an hour old'):
            approve(token)

    def test_rejects_a_proposal_whose_project_left_the_semester(self, proposal, semester):
        semester.projects.remove(proposal.teams[0].project)
        with pytest.raises(ProposalError, match='changed since'):
            approve(proposal.token())
        assert Assignment.objects.count() == 0

    def test_token_carries_semester_and_pairs(self, proposal, semester):
        data = signing.loads(proposal.token(), salt=TOKEN_SALT)
        assert data['semester'] == semester.id
        assert len(data['pairs']) == 2


@pytest.mark.django_db
class TestEdit:
    @pytest.fixture
    def proposal(self, semester, sponsor):
        # Alpha: S0, S1 (first choice). Beta: S2, S3 (first choice). Gamma: no team.
        alpha, beta, _ = make_projects(semester, sponsor, ['Alpha', 'Beta', 'Gamma'])
        for i, s in enumerate(make_students(4)):
            rank(s, *((alpha, beta) if i < 2 else (beta, alpha)))
        return propose(semester, capacity=2)

    @staticmethod
    def ids(proposal):
        alpha, beta = (team.project for team in proposal.teams)
        s0, s1 = (m[0] for m in proposal.teams[0].members)
        s2, s3 = (m[0] for m in proposal.teams[1].members)
        return alpha, beta, s0, s1, s2, s3

    def test_swap_recomputes_ranks_and_saves_nothing(self, proposal):
        alpha, beta, s0, s1, s2, s3 = self.ids(proposal)

        edited = edit(proposal.token(), {s0.id: beta.id, s2.id: alpha.id})

        assert edited.pairs == {s0.id: beta.id, s1.id: alpha.id, s2.id: alpha.id, s3.id: beta.id}
        assert edited.rank_counts == {'first': 2, 'second': 2, 'third': 0, 'unranked': 0}
        assert edited.violations == []
        assert edited.moved == {s0.id, s2.id}
        assert Assignment.objects.count() == 0

    def test_one_move_reports_both_team_sizes(self, proposal):
        _, beta, s0, *_ = self.ids(proposal)

        edited = edit(proposal.token(), {s0.id: beta.id})

        assert edited.violations == ['Alpha has 1 student; the fewest is 2.', 'Beta has 3 students; the most is 2.']

    def test_moves_build_on_the_last_check(self, proposal):
        alpha, beta, s0, _, s2, _ = self.ids(proposal)

        half = edit(proposal.token(), {s0.id: beta.id})
        done = edit(half.token(), {s2.id: alpha.id})

        assert done.violations == []
        assert done.moved == {s0.id, s2.id}

    def test_rejects_a_student_not_in_the_proposal(self, proposal):
        alpha, *_ = self.ids(proposal)
        outsider = Student.objects.create(cwid='99999999', first_name='Out', last_name='Sider', email='out@example.com')
        with pytest.raises(ProposalError, match='not in this proposal'):
            edit(proposal.token(), {outsider.id: alpha.id})

    def test_rejects_a_project_not_on_the_semester(self, proposal, sponsor):
        _, _, s0, *_ = self.ids(proposal)
        elsewhere = Project.objects.create(name='Elsewhere', sponsor=sponsor)
        with pytest.raises(ProposalError, match='not on'):
            edit(proposal.token(), {s0.id: elsewhere.id})

    def test_approve_saves_the_edited_proposal(self, proposal, semester):
        alpha, beta, s0, _, s2, _ = self.ids(proposal)

        approve(edit(proposal.token(), {s0.id: beta.id, s2.id: alpha.id}).token())

        assert Assignment.objects.get(student=s0, semester=semester).project == beta
        assert Assignment.objects.get(student=s2, semester=semester).project == alpha

    def test_approve_refuses_teams_outside_the_size_limits(self, proposal):
        _, beta, s0, *_ = self.ids(proposal)
        with pytest.raises(ProposalError, match='outside the team-size limits'):
            approve(edit(proposal.token(), {s0.id: beta.id}).token())
        assert Assignment.objects.count() == 0

    def test_pending_moves_counts_only_real_changes(self, proposal):
        alpha, beta, s0, s1, *_ = self.ids(proposal)
        assert pending_moves(proposal.token(), {s0.id: alpha.id, s1.id: alpha.id}) == 0
        assert pending_moves(proposal.token(), {s0.id: beta.id, s1.id: alpha.id}) == 1


@pytest.mark.django_db
class TestSemesterAdminFlow:
    @pytest.fixture
    def cohort(self, semester, sponsor):
        alpha, beta = make_projects(semester, sponsor, ['Alpha', 'Beta'])
        for i, s in enumerate(make_students(4)):
            rank(s, *((alpha, beta) if i < 2 else (beta, alpha)))
        return semester

    def run_action(self, client, *semesters, team_size=2, min_size=2):
        return client.post(reverse('admin:project_semester_changelist'), {
            'action': 'propose_assignments',
            'index': 0,
            '_selected_action': [s.id for s in semesters],
            'team_size': team_size,
            'min_size': min_size,
        })

    def test_propose_shows_the_table_and_saves_nothing(self, admin_client, cohort):
        response = self.run_action(admin_client, cohort)

        assert response.status_code == 200
        assert response.templates[0].name == 'admin/project/semester/assignment_proposal.html'
        content = response.content.decode()
        assert 'Alpha' in content and 'Beta' in content
        assert 'First choice: 4' in content
        assert Assignment.objects.count() == 0

    def test_propose_reports_errors_back_on_the_list(self, admin_client, cohort):
        # 4 students, 2 projects of 1: not enough seats.
        response = self.run_action(admin_client, cohort, team_size=1, min_size=1)
        assert response.status_code == 302
        messages = [str(m) for m in response.wsgi_request._messages]
        assert messages == ['4 students but only 2 seats (2 projects of 1). Raise the team size or add projects to the semester.']
        assert Assignment.objects.count() == 0

    def test_propose_needs_exactly_one_semester(self, admin_client, cohort):
        other = Semester.objects.create(semester='Summer', year=cohort.year - 1, assignment_date=timezone.now())
        response = self.run_action(admin_client, cohort, other)
        assert response.status_code == 302
        assert Assignment.objects.count() == 0

    def test_approve_saves_the_proposal(self, admin_client, cohort):
        token = self.run_action(admin_client, cohort).context['proposal'].token()

        response = admin_client.post(reverse('admin:project_semester_approve_assignments'), {'token': token})

        assert response.status_code == 302
        assert response.url.startswith(reverse('admin:project_assignment_changelist'))
        assert Assignment.objects.filter(semester=cohort).count() == 4

    def test_approve_emails_each_assigned_student(self, admin_client, cohort):
        token = self.run_action(admin_client, cohort).context['proposal'].token()

        response = admin_client.post(reverse('admin:project_semester_approve_assignments'), {'token': token})

        assert sorted(m.to[0] for m in mail.outbox) == ['s0@example.com', 's1@example.com', 's2@example.com', 's3@example.com']
        messages = [str(m) for m in response.wsgi_request._messages]
        assert 'Emailed 4 student(s) their assignment. Failed: 0.' in messages

    def test_approve_keeps_assignments_when_mail_is_blocked(self, admin_client, cohort, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = 'smtp.gmail.com'
        settings.ALLOW_STUDENT_EMAILS = False
        token = self.run_action(admin_client, cohort).context['proposal'].token()

        response = admin_client.post(reverse('admin:project_semester_approve_assignments'), {'token': token})

        assert Assignment.objects.filter(semester=cohort).count() == 4
        assert mail.outbox == []
        assert any(str(m).startswith('Students were not emailed') for m in response.wsgi_request._messages)

    def test_approve_requires_assignment_permissions(self, client, cohort):
        token = propose(cohort, capacity=2).token()
        staff = User.objects.create_user('staff', password='pw', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='view_semester'))
        client.force_login(staff)

        response = client.post(reverse('admin:project_semester_approve_assignments'), {'token': token})

        assert response.status_code == 403
        assert Assignment.objects.count() == 0

    def test_approve_ignores_get(self, admin_client):
        response = admin_client.get(reverse('admin:project_semester_approve_assignments'))
        assert response.status_code == 302
        assert Assignment.objects.count() == 0

    def moves_for(self, proposal, changes):
        """The move_<id> fields the proposal page posts: every student, with changes applied."""
        return {f'move_{s}': changes.get(s, p) for s, p in proposal.pairs.items()}

    def test_move_one_student_then_approve(self, admin_client, cohort):
        # PBI-09 (#69): propose, move a student, approve, and the edited teams are saved.
        proposal = self.run_action(admin_client, cohort, team_size=3, min_size=1).context['proposal']
        alpha, beta = (team.project for team in proposal.teams)
        mover = proposal.teams[0].members[0][0]

        rechecked = admin_client.post(reverse('admin:project_semester_edit_assignments'),
                                      {'token': proposal.token(), **self.moves_for(proposal, {mover.id: beta.id})})
        edited = rechecked.context['proposal']
        assert rechecked.status_code == 200
        assert edited.violations == [] and edited.moved == {mover.id}
        assert Assignment.objects.count() == 0

        response = admin_client.post(reverse('admin:project_semester_approve_assignments'),
                                     {'token': edited.token(), **self.moves_for(edited, {})})

        assert response.status_code == 302
        assert Assignment.objects.get(student=mover, semester=cohort).project == beta
        assert Assignment.objects.filter(semester=cohort, project=alpha).count() == 1

    def test_violations_are_shown_and_approve_is_disabled(self, admin_client, cohort):
        proposal = self.run_action(admin_client, cohort).context['proposal']
        beta = proposal.teams[1].project
        mover = proposal.teams[0].members[0][0]

        response = admin_client.post(reverse('admin:project_semester_edit_assignments'),
                                     {'token': proposal.token(), **self.moves_for(proposal, {mover.id: beta.id})})

        content = response.content.decode()
        assert 'Fix these before approving' in content
        assert 'Beta has 3 students; the most is 2.' in content
        assert 'value="Approve and save assignments" class="default"' in content and ' disabled>' in content

    def test_approve_with_unchecked_moves_rechecks_instead_of_saving(self, admin_client, cohort):
        proposal = self.run_action(admin_client, cohort, team_size=3, min_size=1).context['proposal']
        beta = proposal.teams[1].project
        mover = proposal.teams[0].members[0][0]

        response = admin_client.post(reverse('admin:project_semester_approve_assignments'),
                                     {'token': proposal.token(), **self.moves_for(proposal, {mover.id: beta.id})})

        assert response.status_code == 200
        assert response.context['proposal'].moved == {mover.id}
        assert Assignment.objects.count() == 0
        assert any('since the last check' in str(m) for m in response.wsgi_request._messages)
