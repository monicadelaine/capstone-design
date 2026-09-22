"""Role-based access rules for project endpoints.

Roles come from the Auth0 token (see ``user.authentication.UserWrapper``), not from
the database. Any authenticated user may read projects. Only admins and sponsors may
write, and a sponsor may only write projects under their own sponsor record.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from user.models import Sponsor

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
