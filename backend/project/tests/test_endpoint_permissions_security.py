"""Regression tests for SECURITY-02 (#57): role and record ownership enforcement."""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from project.models import Attachment, Feedback, Project, Semester
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
def actors():
    owner = Sponsor.objects.create(email='owner@example.com', first_name='Owner',
                                   last_name='Sponsor', organization='Company A')
    other = Sponsor.objects.create(email='other@example.com', first_name='Other',
                                   last_name='Sponsor', organization='Company B')
    student = Student.objects.create(cwid='78901234', email='student@crimson.ua.edu',
                                     first_name='Test', last_name='Student',
                                     class_code=Student.Class.SENIOR, major_code='CS')
    project = Project.objects.create(name='Owner Project', sponsor=owner)
    foreign = Project.objects.create(name='Other Project', sponsor=other)
    semester = Semester.objects.create(
        semester=Semester.Semester.FALL, year=2026,
        assignment_date=timezone.now() + timedelta(days=7),
    )
    return {
        'owner': owner, 'other': other, 'student': student,
        'project': project, 'foreign': foreign, 'semester': semester,
        'owner_client': client(owner.email, ['sponsor']),
        'other_client': client(other.email, ['sponsor']),
        'student_client': client(student.email, ['student']),
        'admin_client': client('admin@example.com', ['admin']),
        'no_role_client': client('anyone@example.com', []),
    }


def attachment_url(pk=None):
    return reverse('project:attachment-detail', args=[pk]) if pk else reverse('project:attachment-list')


def feedback_url(pk=None):
    return reverse('project:feedback-detail', args=[pk]) if pk else reverse('project:feedback-list')


def test_student_cannot_create_or_delete_attachment(actors):
    obj = Attachment.objects.create(project=actors['project'], link='https://example.com/a')
    resp = actors['student_client'].post(attachment_url(), {
        'project': actors['project'].pk, 'link': 'https://example.com/b',
    }, format='json')
    assert resp.status_code == 403
    assert actors['student_client'].delete(attachment_url(obj.pk)).status_code == 403
    assert Attachment.objects.filter(pk=obj.pk).exists()


def test_owner_can_create_and_delete_own_attachment(actors):
    resp = actors['owner_client'].post(attachment_url(), {
        'project': actors['project'].pk, 'link': 'https://example.com/a',
    }, format='json')
    assert resp.status_code == 201
    attachment_id = resp.data['id']
    delete_response = actors['owner_client'].delete(attachment_url(attachment_id))
    assert delete_response.status_code in (200, 204)
    assert not Attachment.objects.filter(pk=attachment_id).exists()


def test_owner_cannot_create_on_foreign_project(actors):
    resp = actors['owner_client'].post(attachment_url(), {
        'project': actors['foreign'].pk, 'link': 'https://example.com/a',
    }, format='json')
    assert resp.status_code == 400


def test_owner_cannot_modify_foreign_attachment(actors):
    obj = Attachment.objects.create(project=actors['foreign'], link='https://example.com/a')
    assert actors['owner_client'].delete(attachment_url(obj.pk)).status_code == 403
    assert actors['owner_client'].patch(attachment_url(obj.pk), {
        'link': 'https://example.com/b',
    }, format='json').status_code == 403
    assert Attachment.objects.filter(pk=obj.pk).exists()


def test_owner_cannot_move_attachment_to_foreign_project(actors):
    obj = Attachment.objects.create(project=actors['project'], link='https://example.com/a')
    resp = actors['owner_client'].patch(attachment_url(obj.pk), {
        'project': actors['foreign'].pk,
    }, format='json')
    assert resp.status_code == 400
    obj.refresh_from_db()
    assert obj.project_id == actors['project'].pk


def test_only_admin_can_write_unassigned_attachment(actors):
    payload = {'project': None, 'link': 'https://example.com/a'}
    assert actors['owner_client'].post(attachment_url(), payload, format='json').status_code == 400
    assert actors['admin_client'].post(attachment_url(), payload, format='json').status_code == 201


def test_authenticated_student_still_reads_visible_attachment(actors):
    Attachment.objects.create(project=actors['project'], link='https://example.com/a')
    resp = actors['student_client'].get(attachment_url(), {'project': actors['project'].pk})
    assert resp.status_code == 200 and len(resp.data) == 1


def test_rejected_project_direct_download_is_hidden(actors):
    rejected = Project.objects.create(name='Rejected Project', sponsor=actors['owner'],
                                      status=Project.StatusChoices.CANCELLED)
    obj = Attachment.objects.create(project=rejected, link='https://example.com/a')
    url = reverse('project:attachment-download', args=[obj.pk])
    # A missing-file error is expected when the record is visible; a 404 means
    # rejection happened before the file field was accessed.
    assert actors['student_client'].get(url).status_code == 404
    assert actors['other_client'].get(url).status_code == 404
    assert actors['owner_client'].get(url).status_code == 400
    assert actors['admin_client'].get(url).status_code == 400


def test_student_and_roleless_cannot_access_feedback(actors):
    for api in (actors['student_client'], actors['no_role_client']):
        assert api.get(feedback_url()).status_code == 403
        assert api.post(feedback_url(), {}, format='json').status_code == 403


def test_owning_sponsor_can_create_and_read_feedback(actors):
    resp = actors['owner_client'].post(feedback_url(), {
        'sponsor': actors['owner'].pk, 'project': actors['project'].pk,
        'semester': actors['semester'].pk, 'text': 'Good progress',
    }, format='json')
    assert resp.status_code == 201
    assert actors['owner_client'].get(feedback_url(resp.data['id'])).status_code == 200


def test_sponsor_cannot_impersonate_or_write_to_foreign_project(actors):
    base = {'sponsor': actors['owner'].pk, 'project': actors['project'].pk,
            'semester': actors['semester'].pk, 'text': 'Fake'}
    assert actors['owner_client'].post(feedback_url(), {**base, 'sponsor': actors['other'].pk},
                                       format='json').status_code == 400
    assert actors['owner_client'].post(feedback_url(), {**base, 'project': actors['foreign'].pk},
                                       format='json').status_code == 400
    assert Feedback.objects.count() == 0


def test_sponsor_cannot_read_or_modify_others_feedback(actors):
    obj = Feedback.objects.create(sponsor=actors['other'], project=actors['foreign'],
                                  semester=actors['semester'], text='Private')
    assert actors['owner_client'].get(feedback_url()).data == []
    assert actors['owner_client'].get(feedback_url(obj.pk)).status_code == 404
    assert actors['owner_client'].delete(feedback_url(obj.pk)).status_code == 404
    assert Feedback.objects.filter(pk=obj.pk).exists()


def test_sponsor_cannot_reassign_existing_feedback(actors):
    obj = Feedback.objects.create(sponsor=actors['owner'], project=actors['project'],
                                  semester=actors['semester'], text='Own')
    resp = actors['owner_client'].patch(feedback_url(obj.pk), {
        'project': actors['foreign'].pk,
    }, format='json')
    assert resp.status_code == 400
    obj.refresh_from_db()
    assert obj.project_id == actors['project'].pk


def test_admin_can_manage_feedback_for_any_sponsor(actors):
    resp = actors['admin_client'].post(feedback_url(), {
        'sponsor': actors['other'].pk, 'project': actors['foreign'].pk,
        'semester': actors['semester'].pk, 'text': 'Admin note',
    }, format='json')
    assert resp.status_code == 201
    assert actors['admin_client'].get(feedback_url()).status_code == 200
    feedback_id = resp.data['id']
    delete_response = actors['admin_client'].delete(feedback_url(feedback_id))
    assert delete_response.status_code in (200, 204)
    assert not Feedback.objects.filter(pk=feedback_id).exists()
