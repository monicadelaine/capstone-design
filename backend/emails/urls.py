from django.urls import path
from emails import views

app_name = 'emails'

urlpatterns = [
    path(f'{app_name}/send', views.send_email, name='send_email'),
    path(f'{app_name}/sponsor-outreach', views.send_sponsor_outreach, name='send_sponsor_outreach'),
    path(f'{app_name}/project-presentation', views.send_project_presentation, name='send_project_presentation'),
]
