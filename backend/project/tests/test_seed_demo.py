import pytest
from django.core.management import call_command

from project.models import Preference, Project, Semester
from user.models import Student


@pytest.mark.django_db
def test_seed_demo_creates_rankable_data_and_is_rerunnable():
    call_command('seed_demo', students=4)
    call_command('seed_demo', students=4)  # second run must not duplicate anything

    semester = Semester.objects.get()
    assert semester.projects.count() == Project.objects.count() == 16
    assert Student.objects.count() == 4
    for student in Student.objects.all():
        ranks = sorted(Preference.objects.filter(student=student).values_list('rank', flat=True))
        assert ranks == [1] * 5 + [2] * 5 + [3] * 5
