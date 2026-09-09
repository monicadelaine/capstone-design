import re
from django.db import models
from django.core.validators import RegexValidator

# Models are orded by chronological appearance
# Fields are ordered by importance descending


class Sponsor(models.Model):
    """Model representing a project sponsor"""

    first_name = models.CharField(max_length=30)
    """[Required] The sponsors first name"""

    last_name = models.CharField(max_length=30)
    """[Required] The sponsors last name"""

    email = models.EmailField()
    """[Required] The email address for the sponsor"""

    # TODO Add an Organization model, and make this field an FK to an Organization record
    organization = models.TextField(max_length=50, blank=True, null=True)
    """[Optional] A company, school, or other organization the sponsor may be attached to"""

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^(\+?\d{1,2})?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$',
                message='Phone number is invalid. Must be at least 10 digits.'
            )
        ]
    )
    """[Optional] A phone number for the sponsor"""

    projects_allowed = models.SmallIntegerField(default=3)
    """[Default] The number of projects a sponsor is allowed to sponsor"""

    created_at = models.DateTimeField(auto_now_add=True)
    """[Default] Tracks when the record was created"""

    updated_at = models.DateTimeField(auto_now=True)
    """[Default] Tracks when the record was last updated"""

    def name(self):
        """Returns first and last name"""
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.name()

    # Functions
    def clean_phone_number(self):
        """Extract only digits from phone number and validate length"""
        if not self.phone_number:
            return None

        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', self.phone_number)

        # Validate length: allow 10 digits or 11 digits (with leading 1)
        if len(digits_only) not in (10, 11):
            raise ValidationError({
                'phone_number': 'Phone number must contain 10 or 11 digits.'
            })

        # Optional: If 11 digits, ensure it starts with 1 (North American)
        # TODO: add support for other country codes.
        if len(digits_only) == 11 and not digits_only.startswith('1'):
            raise ValidationError({
                'phone_number': '11-digit numbers must start with 1.'
            })

        return digits_only

    def save(self, *args, **kwargs):
        """Clean and normalize phone number before saving"""
        if self.phone_number:
            cleaned = self.clean_phone_number()
            if cleaned:
                self.phone_number = cleaned
            else:
                self.phone_number = None

        super().save(*args, **kwargs)

    def name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.name()


class Student(models.Model):
    """Model representing a student to be assigned to a project"""

    cwid = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^\d{8}$',
                message='CWID must be exactly 8 digits.'
            )
        ]
    )
    """[Required] The student's CWID"""

    first_name = models.CharField(max_length=30)
    """[Required] The student's first name"""

    middle_name = models.CharField(max_length=30, blank=True, null=True)
    """[Optional] The student's middle name"""

    last_name = models.CharField(max_length=30)
    """[Required] The student's last name"""

    preferred_name = models.CharField(max_length=30, blank=True, null=True)
    """[Optional] A students preferred name"""

    email = models.EmailField()
    """[Required] The student's email address"""

    description = models.TextField(blank=True, null=True)
    """[Optional] Attributes or skills of the student"""

    class Class(models.TextChoices):
        FRESHMAN = "FR", "Freshman"
        SOPHOMORE = "SO", "Sophomore"
        JUNIOR = "JR", "Junior"
        SENIOR = "SR", "Senior"
        GRADUATE = "GR", "Graduate"

    class_code = models.CharField(max_length=9, blank=True, null=True, choices=Class.choices, verbose_name='class')
    """[Optional] The student's year/class code"""

    major_code = models.CharField(max_length=3, blank=True, null=True, verbose_name='major')
    """[Optional] The student's major code, such as CS for Computer Science, CYS for Cybersecurity"""

    created_at = models.DateTimeField(auto_now_add=True)
    """[Default] Tracks when the record was created"""

    updated_at = models.DateTimeField(auto_now=True)
    """[Default] Tracks when the record was last updated"""

    def name(self):
        """Returns first and last name"""
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.name()
