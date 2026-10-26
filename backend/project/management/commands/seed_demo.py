"""Fill a local database with demo data: the current semester, sponsors, projects, and
students with ranked preferences.

    python manage.py seed_demo

Safe to run more than once: rows are matched by email, CWID, or name and reused.
Uses example.com addresses only. Never run against production.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from project.models import Preference, Project, Semester
from user.models import Sponsor, Student

SPONSORS = [
    ('Ada', 'Lovelace', 'Analytical Engines Inc.'),
    ('Grace', 'Hopper', 'Compiler Works'),
    ('Alan', 'Turing', 'Bletchley Labs'),
    ('Katherine', 'Johnson', 'Orbital Computing'),
    ('Edsger', 'Dijkstra', 'Shortest Path LLC'),
]
PROJECTS = [
    'Campus Study Room Finder', 'Food Pantry Inventory', 'Lab Equipment Checkout', 'Club Event Planner',
    'Bus Arrival Predictor', 'Research Paper Recommender', 'Tutoring Match', 'Parking Availability Map',
    'Volunteer Hours Tracker', 'Accessible Route Planner', 'Course Syllabus Search', 'Intramural Scheduler',
    'Library Seat Sensor Dashboard', 'Alumni Mentoring Portal', 'Recycling Pickup Optimizer', 'Hackathon Judging Tool',
]
FIRST = ['Avery', 'Blake', 'Casey', 'Devon', 'Emery', 'Finley', 'Gray', 'Harper', 'Indy', 'Jordan',
         'Kai', 'Logan', 'Morgan', 'Noel', 'Oakley', 'Parker', 'Quinn', 'Riley', 'Sage', 'Taylor']


class Command(BaseCommand):
    help = 'Create demo semester, sponsors, projects, and students with preferences (local use only).'

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=20)

    @transaction.atomic
    def handle(self, *args, students, **options):
        now = timezone.now()
        semester, _ = Semester.objects.get_or_create(
            semester=Semester.get_semester_by_date(now), year=now.year,
            defaults={'assignment_date': now + timedelta(days=21)},
        )

        sponsors = [
            Sponsor.objects.get_or_create(
                email=f'{first.lower()}.{last.lower()}@example.com',
                defaults={'first_name': first, 'last_name': last, 'organization': org},
            )[0]
            for first, last, org in SPONSORS
        ]
        projects = []
        for i, name in enumerate(PROJECTS):
            project, _ = Project.objects.get_or_create(
                name=name, sponsor=sponsors[i % len(sponsors)],
                defaults={'description': f'Demo project: {name.lower()}.', 'status': Project.StatusChoices.IN_PROGRESS},
            )
            projects.append(project)
        semester.projects.add(*projects)

        # Same rule as the ranking form: 5 high (1), 5 medium (2), 5 low (3).
        rng = random.Random(495)
        weights = [len(projects) - i for i in range(len(projects))]  # a few projects are popular
        made = 0
        for n in range(students):
            student, created = Student.objects.get_or_create(
                cwid=f'{90000000 + n}',
                defaults={'first_name': FIRST[n % len(FIRST)], 'last_name': f'Demo{n + 1}',
                          'email': f'demo.student{n + 1}@example.com', 'class_code': Student.Class.SENIOR,
                          'major_code': 'CS'},
            )
            if Preference.objects.filter(student=student).exists():
                continue
            picks = []
            while len(picks) < 15:
                p = rng.choices(projects, weights)[0]
                if p not in picks:
                    picks.append(p)
            for i, project in enumerate(picks):
                Preference.objects.create(student=student, project=project, rank=i // 5 + 1)
            made += 1

        self.stdout.write(self.style.SUCCESS(
            f'{semester}: {len(sponsors)} sponsors, {len(projects)} projects, '
            f'{students} students ({made} given new preferences). Deadline {semester.assignment_date:%Y-%m-%d}.'))
