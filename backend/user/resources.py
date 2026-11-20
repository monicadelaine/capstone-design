from django.core.exceptions import ValidationError
from import_export import resources, fields
from user import models


class SponsorResource(resources.ModelResource):
    class Meta:
        model = models.Sponsor


class StudentResource(resources.ModelResource):
    # This class uses import_export.fields to map the CSV field names that come from Blackboard to the field
    # names of the model that we defined in Django
    # This does not prevent importing lists that already use the same attribute naming conventions

    email = fields.Field(
        column_name='EMAIL',
        attribute='email'
    )

    first_name = fields.Field(
        column_name='FIRST_NAME',
        attribute='first_name'
    )

    middle_name = fields.Field(
        column_name='MIDDLE_NAME',
        attribute='middle_name'
    )

    last_name = fields.Field(
        column_name='LAST_NAME',
        attribute='last_name'
    )

    preferred_name = fields.Field(
        column_name='PREF_NAME',
        attribute='preferred_name'
    )

    cwid = fields.Field(
        column_name='CWID',
        attribute='cwid'
    )

    class_code = fields.Field(
        column_name='STU_CLASS_CODE',
        attribute='class_code'
    )

    major_code = fields.Field(
        column_name='MAJR_1_CODE',
        attribute='major_code'
    )

    # A roster must have these columns. The others may be absent; a missing optional column leaves
    # that value unchanged on existing students instead of blanking it.
    REQUIRED_COLUMNS = ('EMAIL', 'FIRST_NAME', 'LAST_NAME', 'CWID')

    def clean_class_code(self, value):
        class_code_map = {
            'Freshman': 'FR',
            'Sophomore': 'SO',
            'Junior': 'JR',
            'Senior': 'SR',
            'Graduate': 'GR'
        }
        return class_code_map.get(value, value)

    def before_import(self, dataset, **kwargs):
        # Exports differ in header case and spacing (and Excel can leave a BOM on the first name).
        dataset.headers = [str(h).lstrip('\ufeff').strip().upper() for h in (dataset.headers or [])]
        missing = [c for c in self.REQUIRED_COLUMNS if c not in dataset.headers]
        if missing:
            raise ValueError(
                f'The file is missing required column(s): {", ".join(missing)}. '
                f'Expected columns: {", ".join(self.REQUIRED_COLUMNS)} (and optionally MIDDLE_NAME, PREF_NAME, '
                'STU_CLASS_CODE, MAJR_1_CODE).'
            )
        self.first_row_of_cwid = {}
        super().before_import(dataset, **kwargs)

    def before_import_row(self, row, row_number=None, **kwargs):
        # Trim every value. Login matches the Auth0 email exactly, and Auth0 emails are lower case.
        for column, value in row.items():
            if isinstance(value, str):
                row[column] = value.strip()
        row['EMAIL'] = row['EMAIL'].lower()
        if 'STU_CLASS_CODE' in row:
            row['STU_CLASS_CODE'] = self.clean_class_code(row['STU_CLASS_CODE'])

        # Rows are matched on CWID, so a repeated CWID would silently overwrite the earlier row.
        first_seen = self.first_row_of_cwid.setdefault(row['CWID'], row_number)
        if row['CWID'] and first_seen != row_number:
            raise ValidationError({'cwid': f'CWID {row["CWID"]} already appears in row {first_seen} of this file.'})
        return row

    def validate_instance(self, instance, import_validation_errors=None, validate_unique=True):
        # Email is not unique in the database, but two students with one email would make login ambiguous.
        errors = dict(import_validation_errors or {})
        if instance.email and models.Student.objects.filter(email=instance.email).exclude(cwid=instance.cwid).exists():
            errors['email'] = ValidationError('This email already belongs to a student with a different CWID.')
        super().validate_instance(instance, errors, validate_unique)

    class Meta:
        model = models.Student
        # Re-importing a roster updates students by CWID instead of trying to create them again.
        import_id_fields = ('cwid',)
        # Check each row with the model's own rules (8-digit CWID, valid email, class and major) so a bad
        # row is reported with its row number and the good rows still import.
        clean_model_instances = True
        # Rows that did not change are listed as skipped.
        skip_unchanged = True
        report_skipped = True
