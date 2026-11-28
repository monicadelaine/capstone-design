"""Student role and roster verification regression tests for Issue #77."""
import pytest

from project.permissions import student_for_user, owns_student_id
from user.authentication import UserWrapper
from user.models import Student

pytestmark = pytest.mark.django_db


def actor(email, roles):
    return UserWrapper({
        'email': email,
        'sub': 'auth0|test',
        'roles': roles,
    })


@pytest.fixture
def roster_student():
    return Student.objects.create(
        cwid='12345678',
        email='approved@crimson.ua.edu',
        first_name='Approved',
        last_name='Student',
    )


def test_approved_student_has_access(roster_student):
    user = actor('approved@crimson.ua.edu', ['student'])
    assert student_for_user(user) == roster_student
    assert owns_student_id(user, roster_student.id)


def test_roleless_roster_member_is_denied(roster_student):
    user = actor(roster_student.email, [])
    assert student_for_user(user) is None
    assert not owns_student_id(user, roster_student.id)


def test_sponsor_role_does_not_grant_student_access(roster_student):
    user = actor(roster_student.email, ['sponsor'])
    assert student_for_user(user) is None
    assert not owns_student_id(user, roster_student.id)


def test_unrostered_student_is_denied(roster_student):
    user = actor('outsider@crimson.ua.edu', ['student'])
    assert student_for_user(user) is None
    assert not owns_student_id(user, roster_student.id)


def test_non_university_email_is_denied_even_if_rostered():
    student = Student.objects.create(
        cwid='87654321',
        email='outsider@example.com',
        first_name='Outside',
        last_name='Student',
    )
    user = actor(student.email, ['student'])
    assert student_for_user(user) is None
    assert not owns_student_id(user, student.id)


def test_student_email_matching_is_case_insensitive(roster_student):
    user = actor('APPROVED@CRIMSON.UA.EDU', ['student'])
    assert student_for_user(user) == roster_student
