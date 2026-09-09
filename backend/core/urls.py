"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

API_PREFIX = 'api/v1/'

# FIXME Update site_url for production
admin.site.site_url = 'http://127.0.0.1:5173'
admin.site.site_header = 'Projects Portal'
admin.site.site_title = 'UA Computer Science Senior Design'

urlpatterns = [
    path('admin/action-forms/', include('django_admin_action_forms.urls')),
    path('admin/', admin.site.urls),

    # Mount app URLConfs
    path(f'{API_PREFIX}', include(('project.urls', 'project'), namespace='project')),
    path(f'{API_PREFIX}', include(('user.urls', 'user'), namespace='user')),
    path(f'{API_PREFIX}', include(('emails.urls', 'emails'), namespace='emails')),
]
