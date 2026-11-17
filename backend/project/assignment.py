"""Propose student-project assignments with OR-Tools CP-SAT (PBI-04, #51).

The admin runs a proposal for a semester, reviews it, can move students between projects
(PBI-09, #69), and approves it. Team sizes come from the semester, and a project can set its
own maximum (PBI-08, #68). Nothing is saved until approval: the proposal travels between
steps as a signed token, and only approval writes Assignment rows.
Model and cost weights: docs/investigations/or-tools-evaluation.md
"""
import time
from dataclasses import dataclass

from django.core import signing
from django.db import transaction
from ortools.sat.python import cp_model

from project.models import Assignment, Preference, Project, Semester
from user.models import Student

# Cost of placing a student on a project they ranked 1, 2, or 3, or did not rank at all.
RANK_COST = {1: 0, 2: 1, 3: 3}
UNRANKED_COST = 10
DEFAULT_TEAM_SIZE = 4

TOKEN_SALT = 'project.assignment-proposal'
TOKEN_MAX_AGE = 60 * 60  # seconds


class ProposalError(Exception):
    """The semester's data cannot produce an assignment. The message is shown to the admin."""


def team_limits(project_id, capacity, min_size, overrides):
    """(fewest, most) students for a project that gets a team. A project's own maximum replaces
    the semester's team size; if that maximum is below the semester minimum, it is the minimum too."""
    most = overrides.get(project_id, capacity)
    return min(min_size, most), most


def solve(prefs, project_ids, capacity=DEFAULT_TEAM_SIZE, min_size=None, overrides=None, time_limit=10.0):
    """Put every student on exactly one project at the lowest total rank cost.

    prefs maps student id -> {project id: rank}. A project gets no students or between
    min_size and capacity of them; min_size defaults to capacity, so every team used is
    exactly that size. overrides maps project id -> that project's own maximum.
    Returns ({student id: project id}, solver status name).
    """
    min_size = capacity if min_size is None else min_size
    overrides = overrides or {}
    if not 1 <= min_size <= capacity:
        raise ProposalError('Minimum team size must be between 1 and the team size.')

    model = cp_model.CpModel()
    x = {(s, p): model.new_bool_var(f'x_{s}_{p}') for s in prefs for p in project_ids}
    for s in prefs:
        model.add_exactly_one(x[s, p] for p in project_ids)
    for p in project_ids:
        used = model.new_bool_var(f'used_{p}')
        size = sum(x[s, p] for s in prefs)
        fewest, most = team_limits(p, capacity, min_size, overrides)
        model.add(size >= fewest * used)
        model.add(size <= most * used)
    model.minimize(sum(RANK_COST.get(prefs[s].get(p), UNRANKED_COST) * var for (s, p), var in x.items()))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sizes = f'{capacity}' if min_size == capacity else f'{min_size} to {capacity}'
        own = ' (some projects have their own maximum)' if overrides else ''
        raise ProposalError(
            f'No assignment puts {len(prefs)} students into teams of {sizes}{own}. '
            'Lower the minimum team size or change the team size.'
        )
    return {s: p for (s, p), var in x.items() if solver.value(var)}, solver.status_name(status)


@dataclass
class Team:
    project: Project
    members: list  # [(Student, rank or None)], best rank first
    fewest: int
    most: int


@dataclass
class Proposal:
    semester: Semester
    teams: list
    unused_projects: list
    status: str
    seconds: float
    capacity: int
    min_size: int
    solver_pairs: dict  # {student id: project id} as the solver proposed it, before any moves
    overrides: dict  # {project id: that project's own maximum team size}

    @property
    def pairs(self):
        return {student.id: team.project.id for team in self.teams for student, _ in team.members}

    @property
    def moved(self):
        """Ids of students the admin moved away from the solver's project."""
        return {s for s, p in self.pairs.items() if self.solver_pairs.get(s) != p}

    @property
    def projects(self):
        """Every project a student can be placed on: those with a team, then those without."""
        return sorted([team.project for team in self.teams] + self.unused_projects, key=lambda p: p.name)

    @property
    def violations(self):
        """Team-size problems that must be fixed before approving."""
        problems = []
        for team in self.teams:
            size = len(team.members)
            if size > team.most:
                problems.append(f'{team.project.name} has {size} students; the most is {team.most}.')
            elif size < team.fewest:
                problems.append(f'{team.project.name} has {size} student{"" if size == 1 else "s"}; '
                                f'the fewest is {team.fewest}.')
        return problems

    @property
    def student_count(self):
        return sum(len(team.members) for team in self.teams)

    @property
    def rank_counts(self):
        """How many students got their first, second, or third choice, or a project they did not rank."""
        names = {1: 'first', 2: 'second', 3: 'third', None: 'unranked'}
        counts = dict.fromkeys(names.values(), 0)
        for team in self.teams:
            for _, rank in team.members:
                counts[names[rank]] += 1
        return counts

    def token(self):
        return signing.dumps({
            'semester': self.semester.id,
            'pairs': [[s, p] for s, p in self.pairs.items()],
            'solver': [[s, p] for s, p in self.solver_pairs.items()],
            'capacity': self.capacity,
            'min_size': self.min_size,
            'overrides': [[p, most] for p, most in self.overrides.items()],
            'status': self.status,
            'seconds': self.seconds,
        }, salt=TOKEN_SALT)


def _load(token):
    try:
        return signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.SignatureExpired:
        raise ProposalError('This proposal is more than an hour old. Run it again.')
    except signing.BadSignature:
        raise ProposalError('This proposal could not be verified. Run it again.')


def _candidate_projects(semester):
    return list(
        semester.projects.exclude(status=Project.StatusChoices.CANCELLED).select_related('sponsor').order_by('name')
    )


def _build(semester, result, prefs, projects, status, seconds, capacity, min_size, solver_pairs, overrides):
    """Turn {student id: project id} into a Proposal with each student's rank of their project."""
    students = Student.objects.in_bulk(list(result))
    teams, unused = [], []
    for project in projects:
        members = [(students[s], prefs.get(s, {}).get(project.id)) for s, p in result.items() if p == project.id]
        if members:
            members.sort(key=lambda m: (m[1] or UNRANKED_COST, m[0].last_name, m[0].first_name))
            teams.append(Team(project, members, *team_limits(project.id, capacity, min_size, overrides)))
        else:
            unused.append(project)
    return Proposal(semester, teams, unused, status, seconds, capacity, min_size, solver_pairs, overrides)


def propose(semester, capacity=None, min_size=None):
    """Solve the semester's assignment. Students are those with preferences for the semester;
    projects are the semester's projects that are not cancelled. Team sizes are the semester's
    team_size and min_team_size unless passed in, and a project's max_team_size replaces the
    maximum for that project. Saves nothing."""
    if capacity is None:
        capacity = semester.team_size
        min_size = semester.min_team_size if min_size is None else min_size
    min_size = capacity if min_size is None else min_size
    projects = _candidate_projects(semester)
    overrides = {p.id: p.max_team_size for p in projects if p.max_team_size}
    prefs = {}
    for student_id, project_id, rank in Preference.objects.filter(semester=semester).values_list(
            'student_id', 'project_id', 'rank'):
        prefs.setdefault(student_id, {})[project_id] = rank

    if not projects:
        raise ProposalError(f'{semester} has no projects. Add projects to the semester first.')
    if not prefs:
        raise ProposalError(f'No student has submitted preferences for {semester}.')
    seats = sum(overrides.get(p.id, capacity) for p in projects)
    if len(prefs) > seats:
        raise ProposalError(
            f'{len(prefs)} students but only {seats} seats on {len(projects)} '
            f'project{"" if len(projects) == 1 else "s"}. Raise the team size or add projects to the semester.'
        )

    started = time.perf_counter()
    result, status = solve(prefs, [p.id for p in projects], capacity, min_size, overrides)
    seconds = time.perf_counter() - started
    return _build(semester, result, prefs, projects, status, seconds, capacity, min_size, dict(result), overrides)


def _apply(data, moves):
    """The token's pairs with moves ({student id: project id}) applied."""
    pairs = {s: p for s, p in data['pairs']}
    unknown = set(moves) - set(pairs)
    if unknown:
        raise ProposalError('A moved student is not in this proposal. Run it again.')
    return {**pairs, **moves}


def pending_moves(token, moves):
    """How many of the posted moves differ from the proposal in the token."""
    pairs = {s: p for s, p in _load(token)['pairs']}
    return sum(1 for s, p in moves.items() if pairs.get(s) != p)


def edit(token, moves):
    """Apply the admin's moves to a proposal and re-check it. Saves nothing; the returned
    Proposal carries a new token, and its violations list any team-size problems."""
    data = _load(token)
    semester = Semester.objects.filter(id=data['semester']).first()
    if semester is None:
        raise ProposalError('Students or projects changed since this proposal was made. Run it again.')
    result = _apply(data, moves)
    if Student.objects.filter(id__in=list(result)).count() != len(result):
        raise ProposalError('Students or projects changed since this proposal was made. Run it again.')
    projects = _candidate_projects(semester)
    if not {p for p in result.values()} <= {p.id for p in projects}:
        raise ProposalError(f'A student was moved to a project that is not on {semester}.')
    prefs = {}
    for student_id, project_id, rank in Preference.objects.filter(
            semester=semester, student_id__in=list(result)).values_list('student_id', 'project_id', 'rank'):
        prefs.setdefault(student_id, {})[project_id] = rank
    solver_pairs = {s: p for s, p in data.get('solver', data['pairs'])}
    overrides = {p: most for p, most in data.get('overrides', [])}
    return _build(semester, result, prefs, projects, data.get('status', ''), data.get('seconds'),
                  data.get('capacity', DEFAULT_TEAM_SIZE), data.get('min_size', DEFAULT_TEAM_SIZE),
                  solver_pairs, overrides)


def approve(token):
    """Save a proposal as Assignment rows, replacing each student's existing assignment for
    the semester. Returns (semester, created count, updated count)."""
    semester, created, updated, _ = approve_with_changes(token)
    return semester, created, updated


def approve_with_changes(token):
    """Same as approve, and also returns the ids of students whose assignment is new or moved
    to a different project (the ones to notify). Returns (semester, created, updated, changed)."""
    data = _load(token)
    semester = Semester.objects.filter(id=data['semester']).first()
    pairs = data['pairs']
    student_ids = {s for s, _ in pairs}
    project_ids = {p for _, p in pairs}
    if (semester is None
            or Student.objects.filter(id__in=student_ids).count() != len(student_ids)
            or semester.projects.filter(id__in=project_ids).count() != len(project_ids)):
        raise ProposalError('Students or projects changed since this proposal was made. Run it again.')
    sizes = {}
    for _, project_id in pairs:
        sizes[project_id] = sizes.get(project_id, 0) + 1
    overrides = {p: most for p, most in data.get('overrides', [])}
    for project_id, size in sizes.items():
        fewest, most = team_limits(project_id, data.get('capacity', size), data.get('min_size', 1), overrides)
        if not fewest <= size <= most:
            raise ProposalError('Some teams are outside the team-size limits. Fix them before approving.')

    created = updated = 0
    changed = []
    with transaction.atomic():
        previous = dict(Assignment.objects.filter(semester=semester, student_id__in=student_ids)
                        .values_list('student_id', 'project_id'))
        for student_id, project_id in pairs:
            _, was_created = Assignment.objects.update_or_create(
                student_id=student_id, semester=semester, defaults={'project_id': project_id}
            )
            if was_created:
                created += 1
            else:
                updated += 1
            if previous.get(student_id) != project_id:
                changed.append(student_id)
    return semester, created, updated, changed
