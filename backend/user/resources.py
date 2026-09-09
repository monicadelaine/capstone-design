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

    def clean_class_code(self, value):
        class_code_map = {
            'Freshman': 'FR',
            'Sophomore': 'SO',
            'Junior': 'JR',
            'Senior': 'SR',
            'Graduate': 'GR'
        }
        return class_code_map.get(value, value)

    def before_import_row(self, row, **kwargs):
        row['STU_CLASS_CODE'] = self.clean_class_code(row.get('STU_CLASS_CODE', ''))
        return row

    class Meta:
        model = models.Student
