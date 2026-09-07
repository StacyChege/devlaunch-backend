from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'developer', 'template', 'status', 'updated_at')
    list_filter = ('status', 'template__category')
    search_fields = ('name', 'slug', 'developer__email')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    raw_id_fields = ('developer', 'template')
