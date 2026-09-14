from django.contrib import admin

from .models import Deployment, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'developer', 'template', 'status', 'updated_at')
    list_filter = ('status', 'template__category')
    search_fields = ('name', 'slug', 'developer__email')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    raw_id_fields = ('developer', 'template')


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('project', 'status', 'is_rollback', 'created_at')
    list_filter = ('status', 'is_rollback')
    search_fields = ('project__name', 'project__slug')
    readonly_fields = ('project', 'status', 'html', 'build_log', 'is_rollback', 'created_at')
    raw_id_fields = ('project',)

    def has_add_permission(self, request):
        # Deployments only ever come from the pipeline, never typed by hand.
        return False
