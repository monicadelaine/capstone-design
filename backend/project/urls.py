from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from .views import AttachmentViewSet, AttachmentDownloadAPIView, ProjectViewSet, AssignmentViewSet, PreferenceAPIView, SemesterViewSet, FeedbackViewSet

app_name = 'project'

router = DefaultRouter()

# For viewsets
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'semesters', SemesterViewSet, basename='semester')
router.register(r'assignments', AssignmentViewSet, basename='assignment')
router.register(r'feedback', FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),

    # For APIViews
    path('attachments/<int:pk>/download/', AttachmentDownloadAPIView.as_view(), name='attachment-download'),
    path('preferences/', PreferenceAPIView.as_view(), name='preference-list'),
    re_path(r'^preferences/(?P<pk>\d+-\d+)/$', PreferenceAPIView.as_view(), name='preference-detail'),
]
