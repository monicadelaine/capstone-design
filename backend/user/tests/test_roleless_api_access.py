"""Roleless-token regression tests. All data is created in Django's test DB."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from user.authentication import UserWrapper
from user.models import Sponsor, Student

pytestmark = pytest.mark.django_db


def client(email, roles):
    api = APIClient()
    api.force_authenticate(user=UserWrapper({
        'email': email, 'sub': f'auth0|{email}', 'roles': roles,
    }))
    return api


@pytest.fixture
def records():
    sponsor = Sponsor.objects.create(email='owner@example.com', first_name='Test', last_name='Sponsor')
    student = Student.objects.create(cwid='12345678', email='student@crimson.ua.edu',
                                     first_name='Test', last_name='Student')
    return sponsor, student


@pytest.mark.parametrize('name', [
    'user:student-list', 'user:sponsor-list', 'user:profile',
    'project:project-list', 'project:attachment-list',
    'project:semester-list', 'project:assignment-list',
    'project:feedback-list', 'project:preference-list',
])
def test_roleless_cannot_read_api(name, records):
    assert client('unassigned@example.com', []).get(reverse(name)).status_code == 403


@pytest.mark.parametrize('name', ['user:student-detail', 'user:sponsor-detail'])
def test_roleless_cannot_read_people(name, records):
    sponsor, student = records
    pk = student.pk if 'student' in name else sponsor.pk
    assert client('unassigned@example.com', []).get(reverse(name, args=[pk])).status_code == 403


@pytest.mark.parametrize('name', [
    'user:student-list', 'user:sponsor-list',
    'project:project-list', 'project:attachment-list',
    'project:semester-list', 'project:assignment-list',
])
def test_roleless_cannot_write(name, records):
    assert client('unassigned@example.com', []).post(reverse(name), {}, format='json').status_code == 403


def test_sponsor_still_reads_sponsor_record(records):
    sponsor, _ = records
    assert client(sponsor.email, ['sponsor']).get(
        reverse('user:sponsor-detail', args=[sponsor.pk])).status_code == 200


def test_admin_still_reads_roster(records):
    assert client('admin@example.com', ['admin']).get(reverse('user:student-list')).status_code == 200
