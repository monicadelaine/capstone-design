from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from emails.utils import email_client
from emails.serializers import EmailSerializer
from project.permissions import IsAdminRole
from user.authentication import Auth0Authentication

# Sending email is an admin action (#43).
ADMIN_ONLY = [IsAuthenticated, IsAdminRole]


@api_view(['GET', 'POST'])
@authentication_classes([Auth0Authentication])
@permission_classes(ADMIN_ONLY)
def send_email(request):
    if request.method == 'GET':
        serializer = EmailSerializer()
        return Response(serializer.data)

    serializer = EmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    subject = serializer.validated_data['subject']
    message = serializer.validated_data['message']
    recipient_list = serializer.validated_data['recipients']
    html_message = serializer.validated_data.get('html_message')

    try:
        email_client.send_email(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            html_message=html_message,
        )
        return Response({'status': 'email sent successfully'})
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([Auth0Authentication])
@permission_classes(ADMIN_ONLY)
def send_sponsor_outreach(request):
    recipients = request.data.get('recipients')
    semester = request.data.get('semester', 'spring')
    collection_date = request.data.get('collection_date', 'TBD')
    from_email = request.data.get('from_email')

    if not recipients:
        return Response(
            {'error': 'recipients are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(',') if r.strip()]

    try:
        email_client.send_sponsor_outreach(
            recipient_list=recipients,
            semester=semester,
            collection_date=collection_date,
            from_email=from_email
        )
        return Response({'status': 'sponsor outreach email sent successfully'})
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([Auth0Authentication])
@permission_classes(ADMIN_ONLY)
def send_project_presentation(request):
    required_fields = ['recipients', 'date', 'time', 'project_name',
                       'project_description', 'contact_name', 'contact_email', 'zoom_details']

    for field in required_fields:
        if not request.data.get(field):
            return Response(
                {'error': f'{field} is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

    recipients = request.data.get('recipients')
    if isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(',') if r.strip()]

    from_email = request.data.get('from_email')

    try:
        email_client.send_project_presentation(
            recipient_list=recipients,
            date=request.data.get('date'),
            time=request.data.get('time'),
            project_name=request.data.get('project_name'),
            project_description=request.data.get('project_description'),
            contact_name=request.data.get('contact_name'),
            contact_email=request.data.get('contact_email'),
            zoom_details=request.data.get('zoom_details'),
            from_email=from_email,
        )
        return Response({'status': 'project presentation email sent successfully'})
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
