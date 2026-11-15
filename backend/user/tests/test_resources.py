import html
import re

import pytest
import tablib
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from user.models import Student
from user.resources import StudentResource

HEADERS = ['EMAIL', 'FIRST_NAME', 'MIDDLE_NAME', 'LAST_NAME', 'PREF_NAME', 'CWID', 'STU_CLASS_CODE', 'MAJR_1_CODE']


def student_row(cwid='10000001', email='ann@crimson.ua.edu', first='Ann', last='Lee', middle='', pref='',
                class_code='Senior', major='CS'):
    return [email, first, middle, last, pref, cwid, class_code, major]


def dataset(rows, headers=HEADERS):
    data = tablib.Dataset(headers=headers)
    for row in rows:
        data.append(row)
    return data


def run(rows, headers=HEADERS):
    return StudentResource().import_data(dataset(rows, headers), dry_run=False, raise_errors=False)


def invalid(result):
    """{data row number: [fields that failed]}"""
    return {row.number: sorted(row.error_dict) for row in result.invalid_rows}


@pytest.mark.django_db
class TestImportColumns:
    def test_a_valid_file_creates_the_students_and_maps_class_names_to_codes(self):
        result = run([
            student_row(),
            student_row(cwid='10000002', email='bob@crimson.ua.edu', first='Bob', last='Ray', middle='Q',
                        pref='Bobby', class_code='Junior', major='CYS'),
        ])

        assert not result.has_errors() and not result.has_validation_errors()
        assert result.totals['new'] == 2
        bob = Student.objects.get(cwid='10000002')
        assert (bob.first_name, bob.middle_name, bob.last_name, bob.preferred_name) == ('Bob', 'Q', 'Ray', 'Bobby')
        assert (bob.class_code, bob.major_code, bob.email) == ('JR', 'CYS', 'bob@crimson.ua.edu')

    @pytest.mark.parametrize('column', ['EMAIL', 'FIRST_NAME', 'LAST_NAME', 'CWID'])
    def test_a_missing_required_column_is_named_and_nothing_is_imported(self, column):
        headers = [h for h in HEADERS if h != column]
        rows = [[v for h, v in zip(HEADERS, student_row()) if h != column]]

        result = run(rows, headers)

        assert result.has_errors()
        assert column in str(result.base_errors[0].error)
        assert Student.objects.count() == 0

    def test_optional_columns_may_be_absent_and_do_not_blank_existing_values(self):
        run([student_row(class_code='Senior', major='CS')])
        headers = ['EMAIL', 'FIRST_NAME', 'LAST_NAME', 'CWID']

        result = run([['ann@crimson.ua.edu', 'Ann', 'Leigh', '10000001']], headers)

        assert result.totals['update'] == 1
        ann = Student.objects.get(cwid='10000001')
        assert (ann.last_name, ann.class_code, ann.major_code) == ('Leigh', 'SR', 'CS')

    @pytest.mark.parametrize('headers', [
        [h.lower() for h in HEADERS],
        [f' {h} ' for h in HEADERS],
        ['﻿' + HEADERS[0]] + HEADERS[1:],
    ], ids=['lower case', 'spaces', 'byte order mark'])
    def test_header_case_spacing_and_a_byte_order_mark_are_tolerated(self, headers):
        result = run([student_row()], headers)

        assert result.totals['new'] == 1
        assert Student.objects.get(cwid='10000001').email == 'ann@crimson.ua.edu'

    def test_values_are_trimmed_and_the_email_is_lower_cased(self):
        run([student_row(email='  Ann.Lee@CRIMSON.UA.EDU ', first=' Ann ', cwid=' 10000001 ')])

        ann = Student.objects.get(cwid='10000001')
        assert (ann.email, ann.first_name) == ('ann.lee@crimson.ua.edu', 'Ann')
        assert Student.objects.filter(email='ann.lee@crimson.ua.edu').exists()


@pytest.mark.django_db
class TestReimport:
    def test_importing_again_updates_by_cwid_and_creates_no_duplicates(self):
        run([student_row(), student_row(cwid='10000002', email='bob@crimson.ua.edu', first='Bob', last='Ray')])

        result = run([student_row(), student_row(cwid='10000002', email='bob@crimson.ua.edu', first='Bob',
                                                 last='Rayford')])

        assert not result.has_errors()
        assert (result.totals['new'], result.totals['update'], result.totals['skip']) == (0, 1, 1)
        assert Student.objects.count() == 2
        assert Student.objects.get(cwid='10000002').last_name == 'Rayford'

    def test_an_unchanged_file_skips_every_row(self):
        rows = [student_row(), student_row(cwid='10000002', email='bob@crimson.ua.edu', first='Bob', last='Ray')]
        run(rows)

        result = run(rows)

        assert (result.totals['new'], result.totals['update'], result.totals['skip']) == (0, 0, 2)
        assert Student.objects.count() == 2

    def test_a_student_with_a_new_email_is_updated_not_duplicated(self):
        run([student_row()])

        run([student_row(email='ann.lee@crimson.ua.edu')])

        assert Student.objects.count() == 1
        assert Student.objects.get(cwid='10000001').email == 'ann.lee@crimson.ua.edu'


@pytest.mark.django_db
class TestBadRows:
    def test_bad_rows_are_reported_with_their_row_number_and_the_good_rows_still_import(self):
        result = run([
            student_row(),                                                    # 1: good
            student_row(cwid='12AB', email='a@crimson.ua.edu'),               # 2: CWID not 8 digits
            student_row(cwid='10000003', email='not-an-email'),               # 3: invalid email
            student_row(cwid='123456789', email='b@crimson.ua.edu'),          # 4: CWID too long
            student_row(cwid='10000004', email='c@crimson.ua.edu', class_code='Super Senior'),  # 5: class
            student_row(cwid='10000005', email='d@crimson.ua.edu', major='COMP'),               # 6: major too long
            student_row(cwid='10000006', email='e@crimson.ua.edu', first='Bob', last='Ray'),    # 7: good
        ])

        assert not result.has_errors()
        assert result.totals['new'] == 2 and result.totals['invalid'] == 5
        assert invalid(result) == {
            2: ['cwid'], 3: ['email'], 4: ['cwid'], 5: ['class_code'], 6: ['major_code'],
        }
        assert sorted(Student.objects.values_list('cwid', flat=True)) == ['10000001', '10000006']

    def test_a_blank_cwid_is_rejected(self):
        result = run([student_row(cwid='')])

        assert invalid(result) == {1: ['cwid']}
        assert Student.objects.count() == 0

    def test_a_repeated_cwid_in_the_file_is_reported_and_the_first_row_is_kept(self):
        result = run([
            student_row(),
            student_row(email='other@crimson.ua.edu', first='Other', last='Person'),
        ])

        assert invalid(result) == {2: ['cwid']}
        assert 'row 1' in str(result.invalid_rows[0].error_dict['cwid'][0])
        assert list(Student.objects.values_list('email', flat=True)) == ['ann@crimson.ua.edu']

    def test_an_email_that_belongs_to_another_cwid_is_rejected(self):
        run([student_row()])

        result = run([student_row(cwid='10000002', first='Bob', last='Ray')])   # same email as Ann

        assert invalid(result) == {1: ['email']}
        assert Student.objects.count() == 1

    def test_changing_a_students_email_to_one_that_is_taken_is_rejected(self):
        run([student_row(), student_row(cwid='10000002', email='bob@crimson.ua.edu', first='Bob', last='Ray')])

        result = run([student_row(cwid='10000002', email='ann@crimson.ua.edu', first='Bob', last='Ray')])

        assert invalid(result) == {1: ['email']}
        assert Student.objects.get(cwid='10000002').email == 'bob@crimson.ua.edu'


@pytest.mark.django_db
class TestImportThroughTheAdmin:
    """The same rules, reached the way the instructor reaches them."""

    CSV = (','.join(HEADERS) + '\n'
           'Ann@crimson.ua.edu,Ann,,Lee,,10000001,Senior,CS\n'
           'bob@crimson.ua.edu,Bob,Q,Ray,Bobby,10000002,Junior,CYS\n').encode()

    @pytest.fixture
    def admin_client(self, client):
        client.force_login(User.objects.create_superuser('boss', 'boss@example.com', 'x'))
        return client

    @staticmethod
    def upload(client, raw):
        page = client.get('/admin/user/student/import/').content.decode()
        file_format = re.search(r'<select name="format".*?<option value="(\d+)"', page, re.S).group(1)
        return client.post('/admin/user/student/import/', {
            'format': file_format,
            'import_file': SimpleUploadedFile('roster.csv', raw, content_type='text/csv'),
        })

    @staticmethod
    def confirm(client, preview):
        hidden = {m.group(1): html.unescape(m.group(2)) for m in re.finditer(
            r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"', preview.content.decode())}
        return client.post('/admin/user/student/process_import/', hidden)

    def test_preview_then_confirm_imports_the_roster(self, admin_client):
        preview = self.upload(admin_client, self.CSV)

        assert preview.status_code == 200
        assert Student.objects.count() == 0                      # the preview saves nothing
        assert self.confirm(admin_client, preview).status_code == 302
        assert sorted(Student.objects.values_list('email', flat=True)) == ['ann@crimson.ua.edu', 'bob@crimson.ua.edu']

    def test_importing_again_through_the_admin_updates_students_by_cwid(self, admin_client):
        self.confirm(admin_client, self.upload(admin_client, self.CSV))
        changed = self.CSV.replace(b',Lee,', b',Leigh,')

        preview = self.upload(admin_client, changed)
        self.confirm(admin_client, preview)

        assert 'name="import_file_name"' in preview.content.decode()          # not an error page
        assert Student.objects.count() == 2
        assert Student.objects.get(cwid='10000001').last_name == 'Leigh'

    def test_a_missing_column_is_named_on_the_page(self, admin_client):
        raw = self.CSV.replace(b'CWID', b'CAMPUS_ID', 1)

        response = self.upload(admin_client, raw)

        assert 'missing required column(s): CWID' in html.unescape(response.content.decode())
        assert 'name="import_file_name"' not in response.content.decode()      # no confirm step
        assert Student.objects.count() == 0

    def test_a_bad_row_is_named_on_the_page(self, admin_client):
        raw = self.CSV + b'cara@crimson.ua.edu,Cara,,Doe,,12AB,Senior,CS\n'

        response = self.upload(admin_client, raw)

        assert 'CWID must be exactly 8 digits.' in html.unescape(response.content.decode())
        assert Student.objects.count() == 0                      # preview only


@pytest.mark.django_db
class TestImportPermission:
    """#66: only an admin can import. Importing a roster creates and updates students, so it takes both
    the add and the change permission on Student."""

    IMPORT_URL = '/admin/user/student/import/'

    @classmethod
    def post_roster(cls, client):
        """Post the roster straight to the import page, the way someone who was refused would try."""
        return client.post(cls.IMPORT_URL, {
            'format': '0',
            'import_file': SimpleUploadedFile('roster.csv', TestImportThroughTheAdmin.CSV, content_type='text/csv'),
        })

    @staticmethod
    def staff(username, *codenames):
        user = User.objects.create_user(username, password='x', is_staff=True)
        user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))
        client = Client()
        client.force_login(user)
        return client

    def test_staff_with_no_permissions_cannot_open_or_use_the_import(self):
        client = self.staff('nobody')

        assert client.get(self.IMPORT_URL).status_code == 403
        assert self.post_roster(client).status_code == 403
        assert Student.objects.count() == 0

    def test_the_confirm_step_cannot_be_replayed_by_someone_who_may_not_import(self):
        boss = Client()
        boss.force_login(User.objects.create_superuser('boss', 'boss@example.com', 'x'))
        preview = TestImportThroughTheAdmin.upload(boss, TestImportThroughTheAdmin.CSV)
        outsider = self.staff('nobody')
        hidden = {m.group(1): html.unescape(m.group(2)) for m in re.finditer(
            r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"', preview.content.decode())}

        response = outsider.post('/admin/user/student/process_import/', hidden)

        assert response.status_code == 403
        assert Student.objects.count() == 0

    @pytest.mark.parametrize('codenames', [
        ('view_student',),
        ('view_student', 'add_student'),
        ('view_student', 'change_student'),
        ('add_student',),
        ('change_student',),
    ], ids=['view only', 'view and add', 'view and change', 'add only', 'change only'])
    def test_a_partial_set_of_student_permissions_is_not_enough(self, codenames):
        client = self.staff('partial', *codenames)

        assert client.get(self.IMPORT_URL).status_code == 403
        assert self.post_roster(client).status_code == 403
        assert Student.objects.count() == 0

    def test_staff_with_add_and_change_permission_can_import(self):
        client = self.staff('registrar', 'view_student', 'add_student', 'change_student')

        preview = TestImportThroughTheAdmin.upload(client, TestImportThroughTheAdmin.CSV)
        confirmed = TestImportThroughTheAdmin.confirm(client, preview)

        assert preview.status_code == 200 and confirmed.status_code == 302
        assert Student.objects.count() == 2

    def test_the_import_button_is_shown_only_to_those_who_may_use_it(self):
        viewer = self.staff('viewer', 'view_student')
        registrar = self.staff('registrar', 'view_student', 'add_student', 'change_student')

        assert 'class="import_link"' not in viewer.get('/admin/user/student/').content.decode()
        assert 'class="import_link"' in registrar.get('/admin/user/student/').content.decode()

