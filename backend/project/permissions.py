"""Role-based access rules for the project API (ADR-002, #43).

Admin and sponsor roles come from the Auth0 token (see ``user.authentication.UserWrapper``).
A student is whoever is on the roster: their token email matches a Student row.

- Projects: any authenticated user reads; admins, or sponsors on their own projects, write.
- Preferences: a student reads and writes only their own; admins see all.
- Assignments: admins see all; a student sees their own and their teammates'; a sponsor
  sees those on their projects. Only admins write.
- Semesters: any authenticated user reads; only admins write.
"""
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


def student_for_user(user):
    """The Student record matching the authenticated user's email, or None.

    Per ADR-002 a student is recognised by being on the roster (Student table), not by a
    role claim the client could influence.
    """
    email = getattr(user, 'email', '') or ''
    if not email:
        return None
    return Student.objects.filter(email__iexact=email).first()


def owns_student_id(user, student_id):
    """True when the user is an admin, or is the student with this id."""
    if is_admin(user):
        return True
    student = student_for_user(user)
    return student is not None and str(student.id) == str(student_id)


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
