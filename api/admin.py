from django.contrib import admin
from .models import Project, Template

admin.site.register(Project)

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_premium', 'is_active', 'created_at']
    list_filter = ['category', 'is_premium', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
