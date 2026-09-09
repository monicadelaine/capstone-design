import datetime
import logging
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from user.models import Sponsor, Student
from project.storage import S3MediaStorage

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_FILE_SIZE = 25 * 1024 * 1024
ALLOWED_ATTACHMENT_FILE_EXTENSIONS = ['pdf', 'docx', 'pptx', 'png', 'jpeg', 'jpg', 'zip']


def validate_attachment_file_size(file_obj):
    if file_obj and file_obj.size > MAX_ATTACHMENT_FILE_SIZE:
        raise ValidationError(f'File size must be {MAX_ATTACHMENT_FILE_SIZE // (1024 * 1024)} MB or less.')

# Models are orded by chronological appearance
# Fields are ordered by importance descending


class Project(models.Model):
    """Model representing a senior design project that students can be assigned to"""

    name = models.CharField(max_length=100)
    """[Required] Project name"""

    description = models.TextField(blank=True, null=True)
    """[Optional] A description of the project"""

    sponsor = models.ForeignKey(
        Sponsor,
        on_delete=models.PROTECT
    )
    """[Required] FK to a Sponsor (on_delete=PROTECT)"""

    sponsor_availability = models.TextField(blank=True, null=True)
    """[Optional] A text field for the sponsor of the project to describe when they are available to meet with the design team"""

    # TODO Convert to a read only field that is based on whether it is assigned during a semester or not
    class StatusChoices(models.TextChoices):
        IN_PROGRESS = 'IP', _('In Progress')
        CANCELLED = 'CNCL', _('Cancelled')
        COMPLETE = 'CMPL', _('Complete')
        PENDING = 'PNDG', _('Pending')

    status = models.CharField(
        max_length=4,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    """[Required] The current status of the project"""

    # TODO Adapt this field to be allowed to support multiple URLs
    #      Remove this field and make it an attachment type
    website = models.URLField(blank=True, null=True)
    """[Optional] A URL field for the project's website"""

    created_at = models.DateTimeField(auto_now_add=True)
    """[Default] Tracks when the record was created"""

    updated_at = models.DateTimeField(auto_now=True)
    """[Default] Tracks when the record was last updated"""

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'sponsor'], name='unique_name_sponsor')
        ]

    def __str__(self):
        return self.name


def attachment_upload_path(instance, filename):
    return f'{instance.project.id}/{filename}'


class Attachment(models.Model):
    # [Optional] FK to a project
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    # [Optional] Stored file attachment. Leave blank when storing a link instead.
    file = models.FileField(
        upload_to=attachment_upload_path,
        storage=S3MediaStorage(),
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_ATTACHMENT_FILE_EXTENSIONS),
            validate_attachment_file_size,
        ],
    )

    # [Optional] Stored hyperlink attachment. Leave blank when uploading a file instead.
    link = models.URLField(blank=True, null=True)

    # [Optional] Title for the attachment (used for email exports)
    title = models.CharField(max_length=255, blank=True, null=True)

    # [Optional] Content for email exports (EML/HTML content stored as text)
    content = models.TextField(blank=True, null=True)

    # [Default] Tracks when the record was created
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        # For email exports, content alone is valid (no file or link needed)
        if self.content:
            return  # Email exports are valid with just content

        # For regular attachments, require either file or link, but not both
        if bool(self.file) == bool(self.link):
            if not self.file and not self.link:
                raise ValidationError('Provide a file, link, or content.')
            elif self.file and self.link:
                raise ValidationError('Provide only a file, link, or content.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file from storage before deleting the record
        if self.file:
            try:
                file_name = self.file.name
                logger.info(f'Deleting attachment file: {file_name}')
                self.file.delete(save=False)
                logger.info(f'Successfully deleted attachment file: {file_name}')
            except Exception as e:
                logger.error(f'Error deleting attachment file {self.file.name}: {str(e)}', exc_info=True)
        super().delete(*args, **kwargs)

    def __str__(self):
        if self.link:
            return f'{self.project} (link)'
        if self.file:
            return f'{self.project}{self.file.name[self.file.name.find("/"):]}'
        return str(self.project)


class Semester(models.Model):
    """Model representing a particular semester over the course of senior design"""

    class Semester(models.TextChoices):
        FALL = 'Fall'
        SPRING = 'Spring'
        SUMMER = 'Summer'

    semester = models.CharField(
        max_length=10,
        choices=Semester.choices,
    )
    """[Required] Fall, Spring, or Summer"""

    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(datetime.date.today().year + 1)],
        help_text='Enter a four-digit year between 1900 and the current or next year'
    )
    """[Required] The year of the semester"""

    assignment_date = models.DateTimeField()
    """[Required] Students must have their preferences submitted by this time"""

    projects = models.ManyToManyField(Project)
    """[Optional] The projects that will be assigned during the semester"""

    created_at = models.DateTimeField(auto_now_add=True)
    """[Default] Tracks when the record was created"""

    updated_at = models.DateTimeField(auto_now=True)
    """[Default] Tracks when the record was last updated"""

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['semester', 'year'], name='unique_semester_year')
        ]

    def __str__(self):
        return f'{self.semester} {self.year}'

    # TODO Add an overload of this method to return a Semester instance rather than the enumerable?
    def get_semester_by_date(date):
        """Helper function to determine the semester given a date"""
        if date.month in [1, 2, 3, 4, 5]:
            return Semester.Semester.SPRING
        elif date.month in [6, 7]:
            return Semester.Semester.SUMMER
        else:
            return Semester.Semester.FALL


class Preference(models.Model):
    """Model representing a student's ranked preference for a project"""

    id = models.SlugField(max_length=64, primary_key=True, editable=False)
    """[Calculated] A slug field that serves as the PK for the model, this is generated from the student and project FKs"""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )
    """[Required] Foreign key to a student"""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    """[Required] Foreign key to a project"""

    class RankChoices(models.IntegerChoices):
        ONE = 1, '1'
        TWO = 2, '2'
        THREE = 3, '3'

    rank = models.PositiveSmallIntegerField(
        choices=RankChoices.choices
    )
    """[Required] Number rank of student's preference toward project, 1 being the first choice"""

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    """[Default] Set using the get_semester function"""

    created_at = models.DateTimeField(auto_now_add=True)
    """[Default] Tracks when the record was created"""

    updated_at = models.DateTimeField(auto_now=True)
    """[Default] Tracks when the record was last updated"""

    def __str__(self):
        return f'{self.student} ({self.project})'

    # Override the model save method to compute the slug from the fields on saving to DB
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.generate_id()
        self.semester = self.get_semester()
        super().save(*args, **kwargs)

    def generate_id(self, student_id=None, project_id=None):
        """Generates a slug from the student and project FKs, this is used as the PK for the model"""
        if (not student_id or not project_id) and self:
            student_id = self.student.id
            project_id = self.project.id
        return slugify(f'{student_id}-{project_id}')

    # TODO Add error handling for when a semester object is not found
    def get_semester(self, date=None):
        """Return a semester object based on the updated date"""
        date = date or self.updated_at or timezone.now()
        return Semester.objects.filter(semester=Semester.get_semester_by_date(date), year=date.year).first()


class Assignment(models.Model):
    """Records a student that has been assigned to a project during a semester"""

    id = models.SlugField(max_length=64, primary_key=True, editable=False)
    """[Calculated] A slug field that serves as the PK for the model, this is generated from the student and semester FKs"""

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE
    )
    """[Required] Foreign key to a semester"""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )
    """[Required] Foreign key to a student"""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    """[Required] Foreign key to a project"""

    created_at = models.DateTimeField(auto_now_add=True)
    """[Default] Tracks when the record was created"""

    updated_at = models.DateTimeField(auto_now=True)
    """[Default] Tracks when the record was last updated"""

    def __str__(self):
        return f'{self.project} -> {self.student} ({self.semester})'

    # Override the model save method to compute the slug from the fields on saving to DB
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.generate_id()
        super().save(*args, **kwargs)

    def generate_id(self, student_id=None, semester_id=None):
        """Generates a slug from the student and semester FKs, this is used as the PK for the model"""
        if (not student_id or not semester_id) and self:
            student_id = self.student.id
            semester_id = self.semester.id
        return slugify(f'{student_id}-{semester_id}')


class Feedback(models.Model):
    """Model representing a note of feedback from a sponsor"""

    sponsor = models.ForeignKey(
        Sponsor,
        on_delete=models.CASCADE
    )
    """[Required] The sponsor that submitted the feedback"""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    """[Required] The project the sponsor is providing feedback on"""

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE
    )
    """[Required] The semester the sponsor is providing feedback on"""

    text = models.TextField()
    """[Required] The feedback"""

    created_at = models.DateTimeField(auto_now_add=True)
    """[Default] Tracks when the record was created"""

    updated_at = models.DateTimeField(auto_now=True)
    """[Default] Tracks when the record was last updated"""

    class Meta:
        verbose_name_plural = 'Feedback'

    def __str__(self):
        return f'{self.sponsor.name()} ({self.id})'
