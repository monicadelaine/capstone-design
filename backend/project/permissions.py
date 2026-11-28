"""Role-based access rules for the project API (ADR-002, #43).

Admin and sponsor roles come from the Auth0 token (see ``user.authentication.UserWrapper``).
A student is whoever is on the roster: their token email matches a Student row.

- Projects: any authenticated user reads; admins, or sponsors on their own projects, write.
  Rejected (Cancelled) projects are visible only to admins and the owning sponsor, and only
  admins approve or reject (#67).
- Preferences: a student reads and writes only their own; admins see all.
- Assignments: admins see all; a student sees their own and their teammates'; a sponsor
  sees those on their projects. Only admins write.
- Semesters: any authenticated user reads; only admins write.
"""
from django.db.models import Q
from rest_framework.permissions import SAFE_METHODS, BasePermission

from user.models import Sponsor, Student

ROLE_ADMIN = 'admin'
ROLE_SPONSOR = 'sponsor'


def user_has_role(user, role):
    """True when the authenticated user carries the given Auth0 role."""
    has_role = getattr(user, 'has_role', None)
    return bool(has_role) and bool(has_role(role))


def is_admin(user):
    return user_has_role(user, ROLE_ADMIN)


def sponsor_for_user(user):
    """The Sponsor record matching the authenticated user's email, or None."""
    email = getattr(user, 'email', '') or ''
    if not email:
        return None
    return Sponsor.objects.filter(email=email).first()


class ProjectWritePermission(BasePermission):
    """Reads are open to any authenticated user.

    Writes need the admin role, or the sponsor role acting on that sponsor's own
    projects. Which sponsor a payload may name, and how many projects a sponsor may
    have, are enforced by ``ProjectSerializer``.
    """

    message = 'Only sponsors may create or change projects, and only their own.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_admin(request.user) or user_has_role(request.user, ROLE_SPONSOR)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or is_admin(request.user):
            return True
        sponsor = sponsor_for_user(request.user)
        return sponsor is not None and obj.sponsor_id == sponsor.id


def hide_rejected_projects(queryset, user, project_path=''):
    """Drop rows whose project was rejected (Cancelled), unless the user is an admin or the
    project's own sponsor (#67). project_path is how the queryset reaches the project, for
    example 'project__' for attachments; empty for a Project queryset."""
    if is_admin(user):
        return queryset
    rejected = Q(**{f'{project_path}status': 'CNCL'})
    sponsor = sponsor_for_user(user)
    if sponsor is not None:
        rejected &= ~Q(**{f'{project_path}sponsor': sponsor})
    return queryset.exclude(rejected)


def student_for_user(user):
    """Return a student only when both trusted role and roster eligibility match.

    A student must have an Auth0 student role, a crimson.ua.edu email,
    and a matching entry in the instructor-managed Student roster.
    """
    if not user_has_role(user, 'student'):
        return None

    email = (getattr(user, 'email', '') or '').strip()
    if not email.lower().endswith('@crimson.ua.edu'):
        return None

    return Student.objects.filter(email__iexact=email).first()


def owns_student_id(user, student_id):
    """True when the user is an admin, or is the student with this id."""
    if is_admin(user):
        return True
    student = student_for_user(user)
    return student is not None and str(student.id) == str(student_id)


class HasAssignedRole(BasePermission):
    """Reject valid Auth0 users with no recognized application role.

    This is a coarse API boundary, not a replacement for object-level
    authorization or university-roster verification.
    """

    message = 'An assigned application role is required.'

    def has_permission(self, request, view):
        return any(user_has_role(request.user, role)
                   for role in ('admin', 'sponsor', 'student'))


class IsAdminRole(BasePermission):
    """Only users carrying the admin role."""

    message = 'Only admins may do this.'

    def has_permission(self, request, view):
        return is_admin(request.user)


class AdminWriteOrReadOnly(BasePermission):
    """Any authenticated user may read; only admins may write."""

    message = 'Only admins may create or change this.'

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_admin(request.user)


class AttachmentWritePermission(BasePermission):
    """Keep authenticated reads; only admins and owning sponsors may write."""

    message = 'Only the owning sponsor or an administrator may modify attachments.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS or is_admin(request.user):
            return True
        return user_has_role(request.user, ROLE_SPONSOR) and sponsor_for_user(request.user) is not None

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or is_admin(request.user):
            return True
        sponsor = sponsor_for_user(request.user)
        return sponsor is not None and obj.project_id is not None and obj.project.sponsor_id == sponsor.id


class SponsorFeedbackPermission(BasePermission):
    """Feedback is private to the owning sponsor; admins can access all."""

    message = 'Only the owning sponsor or an administrator may access feedback.'

    def has_permission(self, request, view):
        if is_admin(request.user):
            return True
        return user_has_role(request.user, ROLE_SPONSOR) and sponsor_for_user(request.user) is not None

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        sponsor = sponsor_for_user(request.user)
        return (sponsor is not None and obj.sponsor_id == sponsor.id
                and obj.project.sponsor_id == sponsor.id)
