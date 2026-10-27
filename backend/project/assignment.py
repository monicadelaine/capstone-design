"""Propose student-project assignments with OR-Tools CP-SAT (PBI-04, #51).

The admin runs a proposal for a semester, reviews it, and approves it. Nothing is saved
until approval: the proposal travels to the approve step as a signed token, and only
approval writes Assignment rows. Model and cost weights: docs/investigations/or-tools-evaluation.md
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


def solve(prefs, project_ids, capacity=DEFAULT_TEAM_SIZE, min_size=None, time_limit=10.0):
    """Put every student on exactly one project at the lowest total rank cost.

    prefs maps student id -> {project id: rank}. A project gets no students or between
    min_size and capacity of them; min_size defaults to capacity, so every team used is
    exactly that size. Returns ({student id: project id}, solver status name).
    """
    min_size = capacity if min_size is None else min_size
    if not 1 <= min_size <= capacity:
        raise ProposalError('Minimum team size must be between 1 and the team size.')

    model = cp_model.CpModel()
    x = {(s, p): model.new_bool_var(f'x_{s}_{p}') for s in prefs for p in project_ids}
    for s in prefs:
        model.add_exactly_one(x[s, p] for p in project_ids)
    for p in project_ids:
        used = model.new_bool_var(f'used_{p}')
        size = sum(x[s, p] for s in prefs)
        model.add(size >= min_size * used)
        model.add(size <= capacity * used)
    model.minimize(sum(RANK_COST.get(prefs[s].get(p), UNRANKED_COST) * var for (s, p), var in x.items()))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sizes = f'{capacity}' if min_size == capacity else f'{min_size} to {capacity}'
        raise ProposalError(
            f'No assignment puts {len(prefs)} students into teams of {sizes}. '
            'Lower the minimum team size or change the team size.'
        )
    return {s: p for (s, p), var in x.items() if solver.value(var)}, solver.status_name(status)


@dataclass
class Team:
    project: Project
    members: list  # [(Student, rank or None)], best rank first


@dataclass
class Proposal:
    semester: Semester
    teams: list
    unused_projects: list
    status: str
    seconds: float
    capacity: int
    min_size: int

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
        pairs = [[student.id, team.project.id] for team in self.teams for student, _ in team.members]
        return signing.dumps({'semester': self.semester.id, 'pairs': pairs}, salt=TOKEN_SALT)


def propose(semester, capacity=DEFAULT_TEAM_SIZE, min_size=None):
    """Solve the semester's assignment. Students are those with preferences for the semester;
    projects are the semester's projects that are not cancelled. Saves nothing."""
    min_size = capacity if min_size is None else min_size
    projects = list(
        semester.projects.exclude(status=Project.StatusChoices.CANCELLED).select_related('sponsor').order_by('name')
    )
    prefs = {}
    for student_id, project_id, rank in Preference.objects.filter(semester=semester).values_list(
            'student_id', 'project_id', 'rank'):
        prefs.setdefault(student_id, {})[project_id] = rank

    if not projects:
        raise ProposalError(f'{semester} has no projects. Add projects to the semester first.')
    if not prefs:
        raise ProposalError(f'No student has submitted preferences for {semester}.')
    seats = capacity * len(projects)
    if len(prefs) > seats:
        raise ProposalError(
            f'{len(prefs)} students but only {seats} seats ({len(projects)} projects of {capacity}). '
            'Raise the team size or add projects to the semester.'
        )

    started = time.perf_counter()
    result, status = solve(prefs, [p.id for p in projects], capacity, min_size)
    seconds = time.perf_counter() - started

    students = Student.objects.in_bulk(list(prefs))
    teams, unused = [], []
    for project in projects:
        members = [(students[s], prefs[s].get(project.id)) for s, p in result.items() if p == project.id]
        if members:
            members.sort(key=lambda m: (m[1] or UNRANKED_COST, m[0].last_name, m[0].first_name))
            teams.append(Team(project, members))
        else:
            unused.append(project)
    return Proposal(semester, teams, unused, status, seconds, capacity, min_size)


def approve(token):
    """Save a proposal as Assignment rows, replacing each student's existing assignment for
    the semester. Returns (semester, created count, updated count)."""
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.SignatureExpired:
        raise ProposalError('This proposal is more than an hour old. Run it again.')
    except signing.BadSignature:
        raise ProposalError('This proposal could not be verified. Run it again.')

    semester = Semester.objects.filter(id=data['semester']).first()
    pairs = data['pairs']
    student_ids = {s for s, _ in pairs}
    project_ids = {p for _, p in pairs}
    if (semester is None
            or Student.objects.filter(id__in=student_ids).count() != len(student_ids)
            or semester.projects.filter(id__in=project_ids).count() != len(project_ids)):
        raise ProposalError('Students or projects changed since this proposal was made. Run it again.')

    created = updated = 0
    with transaction.atomic():
        for student_id, project_id in pairs:
            _, was_created = Assignment.objects.update_or_create(
                student_id=student_id, semester=semester, defaults={'project_id': project_id}
            )
            if was_created:
                created += 1
            else:
                updated += 1
    return semester, created, updated
