"""Authorization regressions for Student and Sponsor record APIs."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.authentication import UserWrapper
from user.models import Sponsor, Student


def client_for(email, roles):
    client = APIClient()
    client.force_authenticate(user=UserWrapper({
        'email': email,
        'sub': f'auth0|{email}',
        'roles': roles,
    }))
    return client


@pytest.fixture
def sponsor(db):
    return Sponsor.objects.create(
        first_name='Alice', last_name='Owner', email='alice@example.com')


@pytest.fixture
def student(db):
    return Student.objects.create(
        cwid='12345678', first_name='Sam', last_name='Student',
        email='sam@example.com')


@pytest.mark.django_db
@pytest.mark.parametrize('role', ['student', 'sponsor'])
def test_non_admin_cannot_create_student(role):
    client = client_for('user@example.com', [role])
    result = client.post(reverse('user:student-list'), {
        'cwid': '87654321', 'first_name': 'New', 'last_name': 'Student',
        'email': 'new.student@example.com'
    }, format='json')
    assert result.status_code == status.HTTP_403_FORBIDDEN
    assert not Student.objects.filter(email='new.student@example.com').exists()


@pytest.mark.django_db
@pytest.mark.parametrize('role', ['student', 'sponsor'])
def test_non_admin_cannot_create_sponsor(role):
    client = client_for('user@example.com', [role])
    result = client.post(reverse('user:sponsor-list'), {
        'first_name': 'New', 'last_name': 'Sponsor',
        'email': 'new.sponsor@example.com'
    }, format='json')
    assert result.status_code == status.HTTP_403_FORBIDDEN
    assert not Sponsor.objects.filter(email='new.sponsor@example.com').exists()


@pytest.mark.django_db
def test_student_cannot_edit_or_delete_another_student(student):
    client = client_for('other@example.com', ['student'])
    url = reverse('user:student-detail', args=[student.pk])
    assert client.patch(url, {'preferred_name': 'Altered'}, format='json').status_code == 403
    assert client.delete(url).status_code == 403
    assert Student.objects.filter(pk=student.pk).exists()


@pytest.mark.django_db
def test_sponsor_cannot_edit_or_delete_another_sponsor(sponsor):
    client = client_for('other@example.com', ['sponsor'])
    url = reverse('user:sponsor-detail', args=[sponsor.pk])
    assert client.patch(url, {'organization': 'Hijacked'}, format='json').status_code == 403
    assert client.delete(url).status_code == 403
    assert Sponsor.objects.filter(pk=sponsor.pk).exists()


@pytest.mark.django_db
def test_admin_can_update_student(student):
    client = client_for('admin@example.com', ['admin'])
    response = client.patch(reverse('user:student-detail', args=[student.pk]),
                            {'preferred_name': 'Updated'}, format='json')
    assert response.status_code == 200
    student.refresh_from_db()
    assert student.preferred_name == 'Updated'


@pytest.mark.django_db
def test_sponsor_can_read_sponsor_record(sponsor):
    client = client_for(sponsor.email, ['sponsor'])
    result = client.get(reverse('user:sponsor-detail', args=[sponsor.pk]))
    assert result.status_code == 200


@pytest.mark.django_db
def test_sponsor_can_update_own_profile_without_record_write_permission(sponsor):
    client = client_for(sponsor.email, ['sponsor'])
    result = client.put(reverse('user:profile'), {'organization': 'Acme'}, format='json')
    assert result.status_code == 200
    sponsor.refresh_from_db()
    assert sponsor.organization == 'Acme'
