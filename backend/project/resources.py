from import_export import resources
from project import models


class ProjectResource(resources.ModelResource):
    class Meta:
        model = models.Project


class AttachmentResource(resources.ModelResource):
    class Meta:
        model = models.Attachment


class SemesterResource(resources.ModelResource):
    class Meta:
        model = models.Semester


class PreferenceResource(resources.ModelResource):
    class Meta:
        model = models.Preference


class AssignmentResource(resources.ModelResource):
    class Meta:
        model = models.Assignment


class FeedbackResource(resources.ModelResource):
    class Meta:
        model = models.Feedback
