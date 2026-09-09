import datetime
import logging

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.authentication import Auth0Authentication

from .models import Assignment, Attachment, Feedback, Preference, Project, Semester
from .serializers import (
    AssignmentSerializer,
    AttachmentSerializer,
    FeedbackSerializer,
    PreferenceSerializer,
    ProjectSerializer,
    SemesterSerializer,
)

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'sponsor', 'status']

    authentication_classes = [Auth0Authentication]
    permission_classes = [IsAuthenticated]

    # TODO Add error handling if a semester DNE for the current date
    def list(self, request, *args, **kwargs):
        """Override list method to filter projects by current semester."""
        semester = Semester.objects.filter(semester=Semester.get_semester_by_date(
            datetime.datetime.now()), year=datetime.datetime.now().year).first()
        queryset = self.filter_queryset(self.get_queryset().filter(semester=semester))
        serializer = ProjectSerializer(queryset, many=True)
        return Response(serializer.data)


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']

    authentication_classes = [Auth0Authentication]
    permission_classes = [IsAuthenticated]


class AttachmentDownloadAPIView(APIView):
    authentication_classes = [Auth0Authentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        attachment = get_object_or_404(Attachment, pk=pk)
        if not attachment.file:
            return Response({'error': 'This attachment does not have a file.'}, status=status.HTTP_400_BAD_REQUEST)

        file_handle = attachment.file.open('rb')
        filename = attachment.file.name.rsplit('/', 1)[-1]
        return FileResponse(file_handle, as_attachment=False, filename=filename)


class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['semester', 'year']

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Returns a semester based on the current date"""
        semester = Semester.objects.filter(semester=Semester.get_semester_by_date(
            datetime.datetime.now()), year=datetime.datetime.now().year).first()
        serializer = SemesterSerializer(semester)
        return Response(serializer.data)


class PreferenceAPIView(APIView):
    authentication_classes = [Auth0Authentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, format=None):
        if pk:
            preference = get_object_or_404(Preference, pk=pk)
            serializer = PreferenceSerializer(preference)
            return Response(serializer.data)
        else:
            preferences = Preference.objects.all()
            serializer = PreferenceSerializer(preferences, many=True)
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if isinstance(request.data, dict):
            serializer = PreferenceSerializer(data=request.data)
            logger.debug('Using PreferenceSerializer')
        elif isinstance(request.data, list):
            serializer = PreferenceSerializer(data=request.data, many=True)
            logger.debug('Using PreferenceListSerializer')
        else:
            return Response({'message': f'Request Data was of unexpected type: {type(request.data)}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.debug(serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.warning(ex)
            return Response({'exception': str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None, *args, **kwargs):
        if isinstance(request.data, dict):
            if not pk and 'id' not in request.data:
                # TODO Add regex to validate the presence of a enough data to construct the pk
                #      Really this should be put requests only without the PK and patch only with the PK url
                if 'student' in request.data and 'project' in request.data:
                    pk = f"{request.data['student']}-{request.data['project']}"
                    logger.debug(f'Constructed PK: {pk}')
                else:
                    return Response({'error': f'Missing student or project info: {request.data}'}, status=status.HTTP_400_BAD_REQUEST)

            if not pk:
                pk = request.data['id']

            preference = get_object_or_404(Preference, pk=pk)
            serializer = PreferenceSerializer(preference, data=request.data, partial=True)

        elif isinstance(request.data, list):
            preferences = []

            for preference in request.data:
                if 'id' not in preference and 'student' not in preference and 'project' not in preference:
                    return Response({'error': f'Missing ID: {request.data}'}, status=status.HTTP_400_BAD_REQUEST)
                elif 'id' not in preference:
                    logger.debug(f'request.data:\n{request.data}')
                    preference['id'] = Preference.generate_id(
                        self=None, student_id=preference['student'], project_id=preference['project'])

                updated = get_object_or_404(Preference, pk=preference['id'])
                updated.rank = preference['rank']
                preferences.append(updated)

            logger.debug(preferences)
            serializer = PreferenceSerializer(preferences, data=request.data, many=True, partial=True)

        else:
            return Response({'error': f'Request Data was of unexpected type: {type(request.data)}'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            logger.debug('Serializer reports valid data')
            # TODO Check if any fields actually changed and return 400 if not

            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({'error': f'Missing id of preference to delete!'}, status=status.HTTP_400_BAD_REQUEST)

        preference = get_object_or_404(Preference, pk=pk)
        preference.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['semester', 'student', 'project']

    authentication_classes = [Auth0Authentication]
    permission_classes = [IsAuthenticated]


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sponsor', 'project', 'semester']

    authentication_classes = [Auth0Authentication]
    permission_classes = [IsAuthenticated]
