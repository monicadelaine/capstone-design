from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from emails.utils import email_client
from emails.serializers import EmailSerializer
from project.models import Attachment


@api_view(['GET', 'POST'])
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
def send_sponsor_outreach(request):
    recipients = request.data.get('recipients')
    semester = request.data.get('semester', 'spring')
    collection_date = request.data.get('collection_date', 'Spring 2025 (1/14/25)')
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


@api_view(['GET'])
def export_sponsor_outreach(request):
    semester = request.query_params.get('semester', 'spring')
    collection_date = request.query_params.get('collection_date', 'TBD')

    html_content = email_client.render_sponsor_outreach_html(semester, collection_date)

    attachment = Attachment.objects.create(
        title=f"Sponsor Outreach Email - {semester.capitalize()} {collection_date}",
        content=html_content
    )

    return Response({
        'id': attachment.id,
        'title': attachment.title,
        'content': html_content,
        'download_url': f'/api/v1/projects/attachments/{attachment.id}/download/'
    })


@api_view(['GET'])
def export_project_presentation(request):
    context = {
        'date': request.query_params.get('date', 'TBD'),
        'time': request.query_params.get('time', 'TBD'),
        'project_name': request.query_params.get('project_name', 'TBD'),
        'project_description': request.query_params.get('project_description', 'TBD'),
        'contact_name': request.query_params.get('contact_name', 'TBD'),
        'contact_email': request.query_params.get('contact_email', 'TBD'),
        'zoom_details': request.query_params.get('zoom_details', 'TBD'),
    }

    html_content = email_client.render_project_presentation_html(**context)

    attachment = Attachment.objects.create(
        title=f"Project Presentation Email - {context['project_name']}",
        content=html_content
    )

    return Response({
        'id': attachment.id,
        'title': attachment.title,
        'content': html_content,
        'download_url': f'/api/v1/projects/attachments/{attachment.id}/download/'
    })
