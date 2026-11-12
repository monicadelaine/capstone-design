"""Instructor review of submitted projects (PBI-07, #67).

A sponsor's project starts as Pending and on no semester, so students do not see it.
Approving puts it on a semester, which is what makes it appear in the students' project
list. Rejecting marks it Cancelled and takes it off every semester. Used by the API
(ProjectViewSet.pending / approve / reject) and by the Project admin actions.
"""
from django.db import transaction
from django.utils import timezone

from project.models import Assignment, Project, Semester


class ReviewError(Exception):
    """The project cannot be approved or rejected. The message is shown to the admin."""


def current_semester():
    now = timezone.now()
    return Semester.objects.filter(semester=Semester.get_semester_by_date(now), year=now.year).first()


def pending_projects():
    """Projects waiting for review: still Pending and not on any semester yet."""
    return (Project.objects.filter(status=Project.StatusChoices.PENDING, semester__isnull=True)
            .select_related('sponsor').order_by('created_at'))


@transaction.atomic
def approve_project(project, semester=None):
    """Put the project on the semester (default: the current one) so students can see it.
    Approving a rejected project restores it to Pending. Returns the semester."""
    semester = semester or current_semester()
    if semester is None:
        raise ReviewError('There is no semester for the current date. Create the semester first.')
    if project.status == Project.StatusChoices.CANCELLED:
        project.status = Project.StatusChoices.PENDING
        project.save()
    semester.projects.add(project)
    return semester


@transaction.atomic
def reject_project(project):
    """Mark the project Cancelled and take it off every semester, so students never see it."""
    if Assignment.objects.filter(project=project).exists():
        raise ReviewError(f'{project.name} already has students assigned. Reassign them before rejecting it.')
    project.status = Project.StatusChoices.CANCELLED
    project.save()
    project.semester_set.clear()
    return project
