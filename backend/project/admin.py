import logging
import mimetypes

from django import forms
from django.contrib import admin
from django.db.models import Count, Exists, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django_admin_action_forms import AdminActionForm, action_with_form
from import_export.admin import ImportExportModelAdmin

from project.models import Project, Semester, Preference, Assignment, Feedback, Attachment
from project.resources import ProjectResource, SemesterResource, PreferenceResource, AssignmentResource, FeedbackResource, AttachmentResource

logger = logging.getLogger(__name__)


@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    class SemesterFilter(admin.SimpleListFilter):
        """This filter class is needed because the of the MtM relationship between semesters and projects"""

        title = 'Semester'
        parameter_name = 'semester'

        def lookups(self, request, model_admin):
            # Get unique semesters
            semesters = Semester.objects.distinct()
            return [(semester.id, semester) for semester in semesters]

        def queryset(self, request, queryset):
            # Filter projects by the selected semester
            if self.value():
                return Semester.objects.filter(id=self.value()).first().projects.all()
            return queryset

    resource_classes = [ProjectResource]

    # TODO Add count of preferences, average rank of preferences
    list_display = ['name', 'sponsor_link', 'status', 'semesters']
    list_filter = ['status', SemesterFilter, 'sponsor']
    search_fields = ['name', 'sponsor', 'description']
    # TODO Order by rank of preferences
    ordering = ['-status', 'name']

    class ChangeProjectStatusActionForm(AdminActionForm):
        status = forms.ChoiceField(
            label="Status",
            choices=Project.StatusChoices,
            required=True
        )

    class AssignProjectToSemesterActionForm(AdminActionForm):
        semester = forms.ModelMultipleChoiceField(
            queryset=Semester.objects.all(),
            required=True
        )

        class Meta:
            autocomplete_fields = filter_horizontal = ['semester']

    class RemoveProjectFromSemesterActionForm(AdminActionForm):
        class Meta:
            list_objects = True
            help_text = 'Are you sure you want to remove these projects from this semester?'

    @admin.display(description='Sponsor')
    def sponsor_link(self, obj):
        url = reverse('admin:user_sponsor_change', args=[obj.sponsor.id])
        return format_html(f'<a href="{url}">{obj.sponsor}</a>')

    @action_with_form(ChangeProjectStatusActionForm, description='Change status')
    def change_project_status_action(self, request, queryset, data):
        for project in queryset:
            project.status = data['status']
            project.save()
        self.message_user(request, f'Status changed to {data["status"].upper()} for {queryset.count()} projects.')

    @action_with_form(AssignProjectToSemesterActionForm, description='Assign to a semester')
    def assign_project_to_semester(self, request, queryset, data):
        for semester in data['semester']:
            semester.projects.add(*queryset)
            semester.save()
        self.message_user(request, f'Assigned {queryset.count()} projects to {len(data["semester"])} semesters.')

    @action_with_form(RemoveProjectFromSemesterActionForm, description='Remove from semester')
    def remove_project_from_semester(self, request, queryset, data):
        semester_id = request.GET.get('semester')
        if semester_id:
            semester = Semester.objects.filter(id=semester_id).first()
            if semester:
                semester.projects.remove(*queryset)
                semester.save()
            self.message_user(request, f'Removed {queryset.count()} projects from {semester}.')
        else:
            self.message_user(request, 'Filter the projects by a semester first', level='error')

    def semesters(self, obj):
        return Semester.objects.filter(projects=obj).count()

    actions = [change_project_status_action, assign_project_to_semester, remove_project_from_semester]


@admin.register(Attachment)
class AttachmentAdmin(ImportExportModelAdmin):
    resource_classes = [AttachmentResource]

    list_display = ['id', 'title', 'project', 'type_badge', 'file_type_badge', 'download_button', 'created_at']
    list_filter = ['project', 'created_at']
    search_fields = ['title', 'content', 'link']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['accepted_file_types'] = [
            {'ext': 'pdf', 'name': 'PDF Document', 'color': '#dc3545'},
            {'ext': 'docx', 'name': 'Word Document', 'color': '#007bff'},
            {'ext': 'pptx', 'name': 'PowerPoint', 'color': '#d63384'},
            {'ext': 'png', 'name': 'PNG Image', 'color': '#28a745'},
            {'ext': 'jpeg/jpg', 'name': 'JPEG Image', 'color': '#20c997'},
            {'ext': 'zip', 'name': 'ZIP Archive', 'color': '#6c757d'},
        ]
        return super().changelist_view(request, extra_context)

    @admin.display(description='Type')
    def type_badge(self, obj):
        if obj.content:
            if obj.content.strip().startswith(('Subject:', 'To:', 'From:', 'Return-Path:')):
                return format_html('<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 3px;">EML</span>')
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">HTML</span>')
        if obj.file:
            return format_html('<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 3px;">File</span>')
        if obj.link:
            return format_html('<span style="background: #ffc107; color: black; padding: 3px 8px; border-radius: 3px;">Link</span>')
        return '-'

    @admin.display(description='File Type')
    def file_type_badge(self, obj):
        if not obj.file:
            return '-'
        filename = obj.file.name.lower()
        if filename.endswith('.pdf'):
            return format_html('<span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">PDF</span>')
        if filename.endswith('.docx'):
            return format_html('<span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">DOCX</span>')
        if filename.endswith('.pptx'):
            return format_html('<span style="background: #d63384; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">PPTX</span>')
        if filename.endswith('.png'):
            return format_html('<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">PNG</span>')
        if filename.endswith('.jpg') or filename.endswith('.jpeg'):
            return format_html('<span style="background: #20c997; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">JPEG</span>')
        if filename.endswith('.zip'):
            return format_html('<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">ZIP</span>')
        ext = filename.split('.')[-1] if '.' in filename else '?'
        return format_html('<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>', ext.upper())

    @admin.display(description='Download')
    def download_button(self, obj):
        if obj.content or obj.file:
            url = reverse('admin:project_attachment_download', args=[obj.pk])
            return format_html('<a href="{}" target="_blank" rel="noopener noreferrer" class="button" style="padding: 5px 10px; background: #007bff; color: white; text-decoration: none; border-radius: 3px;">Download</a>', url)
        if obj.link:
            return format_html('<a href="{}" target="_blank" class="button" style="padding: 5px 10px; background: #ffc107; color: black; text-decoration: none; border-radius: 3px;">Open Link</a>', obj.link)
        return '-'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/download/', self.admin_site.admin_view(self.download_view), name='project_attachment_download'),
        ]
        return custom_urls + urls

    def download_view(self, request, pk):
        from django.http import HttpResponse, Http404

        attachment = self.get_object(request, pk)
        if not attachment:
            raise Http404('Attachment not found')

        if attachment.content:
            content = attachment.content
            # Check if it's an EML file (starts with headers like Subject:, To:, etc.)
            if content.strip().startswith(('Subject:', 'To:', 'From:', 'Return-Path:')):
                content_type = 'message/rfc822'
                filename = f"{attachment.title or 'email'}.eml"
                should_render_inline = False
            else:
                # It's HTML content
                content_type = 'text/html'
                filename = f"{attachment.title or 'email'}.html"
                should_render_inline = True
        elif attachment.file:
            content = attachment.file.read()
            filename = attachment.file.name.split('/')[-1]
            guessed_type, _ = mimetypes.guess_type(filename)
            content_type = guessed_type or 'application/octet-stream'

            inline_types = {
                'application/pdf',
                'application/json',
                'application/xml',
                'text/plain',
                'text/csv',
                'text/html',
            }
            should_render_inline = (
                content_type in inline_types
                or content_type.startswith('image/')
                or content_type.startswith('text/')
                or content_type.startswith('audio/')
                or content_type.startswith('video/')
            )
        elif attachment.link:
            # Redirect to external link if it's a link
            from django.shortcuts import redirect
            return redirect(attachment.link)
        else:
            raise Http404('No content available')

        response = HttpResponse(content, content_type=content_type)
        disposition = 'inline' if should_render_inline else 'attachment'
        response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        return response


@admin.register(Semester)
class SemesterAdmin(ImportExportModelAdmin):
    resource_classes = [SemesterResource]

    # TODO Add total preferences submitted and number of students with preferences submitted
    list_display = ['semester', 'year', 'assignment_date', 'projects_count']
    list_filter = search_fields = ['year', 'semester']

    @admin.display(description='Projects')
    def projects_count(self, obj):
        url = (reverse('admin:project_project_changelist') + '?' + urlencode({'semester': obj.id}))
        count = obj.projects.count()
        return format_html(f'<a href="{url}">{count}</a>')


@admin.register(Preference)
class PreferenceAdmin(ImportExportModelAdmin):
    class IsAssignedFilter(admin.SimpleListFilter):
        title = 'Student Assigned'
        parameter_name = 'is_assigned'

        def lookups(self, request, model_admin):
            return [('true', 'Assigned'), ('false', 'Not Assigned')]

        def queryset(self, request, queryset):
            assignment_qs = Assignment.objects.filter(
                student=OuterRef('student'),
                semester=OuterRef('semester')
            )
            queryset = queryset.annotate(_is_assigned=Exists(assignment_qs))

            if self.value() == 'true':
                return queryset.filter(_is_assigned=True)
            elif self.value() == 'false':
                return queryset.filter(_is_assigned=False)
            return queryset

    class ProjectFilter(admin.SimpleListFilter):
        title = 'Project'
        parameter_name = 'project'

        def lookups(self, request, model_admin):
            semester_id = request.GET.get('semester__id__exact')
            if semester_id:
                # If a semester filter is applied, only show projects for that semester with the count of assigned students in parentheses

                semester = Semester.objects.filter(id=semester_id).first()
                projects = semester.projects.all() if semester else Project.objects.none()

                assigned_count_qs = Assignment.objects.filter(
                    semester_id=semester_id,
                    project_id=OuterRef('pk')
                ).values('project_id').annotate(count=Count('*')).values('count')

                projects = projects.annotate(
                    num_assigned=Coalesce(
                        Subquery(assigned_count_qs, output_field=IntegerField()),
                        0,
                    )
                )
                return [(project.id, f'{project.name} ({project.num_assigned})') for project in projects.order_by('name')]
            else:
                # else return all projects without counts since we don't know the semester context
                projects = Project.objects.all()

            return [(project.id, project.name) for project in projects.order_by('name')]

        def queryset(self, request, queryset):
            if self.value():
                return queryset.filter(project_id=self.value())
            return queryset

    resource_classes = [PreferenceResource]
    readonly_fields = ['student', 'project', 'semester']

    list_display = ['student', 'project', 'rank', 'semester', 'is_assigned', 'assigned_to_project']
    ordering = ['created_at']
    list_filter = ['semester', IsAssignedFilter, 'rank', ProjectFilter]

    # TODO Search fields by semester, project, student
    search_fields = ['student', 'project']

    class AssignStudentToProject(AdminActionForm):
        project = forms.ModelChoiceField(
            queryset=Project.objects.all(),
            required=True,
            empty_label='Select project',
        )

    @action_with_form(AssignStudentToProject, description='Assign to project')
    def assign_to_project(self, request, queryset, data):
        selected_project = data['project']

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        missing_semester_count = 0
        seen = set()

        for preference in queryset.select_related('student', 'semester'):
            if preference.student_id in seen:
                self.message_user(
                    request,
                    'Select each student only once before assigning them to a project.',
                    level='error'
                )
                return

            seen.add(preference.student_id)

            if preference.semester is None:
                missing_semester_count += 1
                continue

            assignment, created = Assignment.objects.get_or_create(
                student=preference.student,
                semester=preference.semester,
                defaults={'project': selected_project}
            )

            if created:
                created_count += 1
            elif assignment.project_id != selected_project.id:
                assignment.project = selected_project
                assignment.save()
                updated_count += 1
            else:
                unchanged_count += 1

        self.message_user(
            request,
            (
                f'Assigned selected students to {selected_project}. '
                f'Created: {created_count}, Updated: {updated_count}, '
                f'Already on project: {unchanged_count}, '
                f'Skipped (no semester): {missing_semester_count}.'
            )
        )

    actions = [assign_to_project]

    def is_assigned(self, obj):
        count = Assignment.objects.filter(student=obj.student, semester=obj.semester).count()
        if count == 1:
            return True
        elif count == 0:
            return False
        else:
            logger.error(f'Student {obj.student} has multiple assignments ({count}) for semester {obj.semester}')
            return None

    def assigned_to_project(self, obj):
        return Assignment.objects.filter(project=obj.project, semester=obj.semester).count()


@admin.register(Assignment)
class AssignmentAdmin(ImportExportModelAdmin):
    resource_classes = [AssignmentResource]
    readonly_fields = ['student', 'project', 'semester']

    list_display = ['project', 'student', 'semester']
    list_filter = ordering = ['semester', 'project']
    search_fields = ['student', 'project']


@admin.register(Feedback)
class FeedbackAdmin(ImportExportModelAdmin):
    resource_classes = [FeedbackResource]
    readonly_fields = ['sponsor', 'project', 'semester']

    list_display = search_fields = ordering = ['id', 'sponsor', 'project']
    list_filter = ['sponsor', 'project', 'semester']
