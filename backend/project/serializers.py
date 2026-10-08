from django.core.validators import FileExtensionValidator
from django.urls import reverse
from rest_framework.serializers import FileField, ModelSerializer, CharField, ListSerializer, ValidationError, DateTimeField, SerializerMethodField
from rest_framework.validators import UniqueTogetherValidator
from .models import Attachment, Semester, Preference, Project, Assignment, Feedback, ALLOWED_ATTACHMENT_FILE_EXTENSIONS, validate_attachment_file_size
from .permissions import ROLE_SPONSOR, is_admin, sponsor_for_user, user_has_role
import logging

logger = logging.getLogger(__name__)


class ProjectSerializer(ModelSerializer):
    status = CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Project.objects.all(),
                fields=['name', 'sponsor'],
                message='You already have a project with this name.',
            ),
        ]

    def _acting_sponsor(self):
        """The request user when they hold the sponsor role without admin rights, else None."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or is_admin(user) or not user_has_role(user, ROLE_SPONSOR):
            return None
        return user

    def validate_sponsor(self, sponsor):
        """A sponsor may only name their own sponsor record; admins may name any."""
        user = self._acting_sponsor()
        if user is not None:
            own = sponsor_for_user(user)
            if own is None or own.id != sponsor.id:
                raise ValidationError('You can only submit projects under your own sponsor account.')
        return sponsor

    def validate(self, attrs):
        """On create, hold sponsors to their projects_allowed limit. Admins are exempt."""
        if self.instance is None and self._acting_sponsor() is not None:
            sponsor = attrs.get('sponsor')
            if sponsor is not None:
                existing = Project.objects.filter(sponsor=sponsor).count()
                if existing >= sponsor.projects_allowed:
                    raise ValidationError({
                        'sponsor': (
                            f'You have reached the maximum of {sponsor.projects_allowed} projects. '
                            'Contact the instructor if you need to submit more.'
                        )
                    })
        return attrs


class AttachmentSerializer(ModelSerializer):
    file = FileField(
        required=False,
        allow_null=True,
        use_url=False,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_ATTACHMENT_FILE_EXTENSIONS),
            validate_attachment_file_size,
        ],
    )
    url = SerializerMethodField()

    def get_url(self, obj):
        if obj.link:
            return obj.link

        request = self.context.get('request')
        url = reverse('project:attachment-download', args=[obj.pk])
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        file_obj = attrs.get('file', getattr(instance, 'file', None))
        link = attrs.get('link', getattr(instance, 'link', None))

        if bool(file_obj) == bool(link):
            raise ValidationError('Provide either a file or a link, but not both.')

        return attrs

    class Meta:
        model = Attachment
        fields = '__all__'


class SemesterSerializer(ModelSerializer):
    # Keep Browsable API form rendering stable when no value is supplied on create forms.
    assignment_date = DateTimeField(style={'input_type': 'text'})

    class Meta:
        model = Semester
        fields = '__all__'


class PreferenceListSerializer(ListSerializer):
    def create(self, validated_data):
        preferences = [Preference(**item) for item in validated_data]
        for preference in preferences:
            preference.id = preference.generate_id()

        return Preference.objects.bulk_create(preferences)

    def update(self, instance, validated_data):
        updates = [Preference(**item) for item in validated_data]
        for update in updates:
            for pref in instance:
                if pref.student == update.student and pref.project == update.project:
                    pref.rank = update.rank
                    break

        return Preference.objects.bulk_update(instance, fields=['rank'], batch_size=100)

    def validate(self, attrs):
        if not self.partial:
            # Only allow submitting one students preferences at a time
            student = [item.get('student') for item in attrs]
            if len(set(student)) != 1:
                raise ValidationError(f'Only 1 student may be updated at a time. Students submitted: {set(student)}')

            # Ensure unique projects
            projects = [item.get('project') for item in attrs]
            if len(projects) != len(set(projects)):
                raise ValidationError(f'Only 1 preference per project may be submitted. Projects submitted: {projects}')

        return attrs


class PreferenceSerializer(ModelSerializer):
    class Meta:
        model = Preference
        fields = '__all__'
        # Instantiating with many=True routes to the PreferenceListSerializer
        list_serializer_class = PreferenceListSerializer


class AssignmentSerializer(ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'


class FeedbackSerializer(ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
