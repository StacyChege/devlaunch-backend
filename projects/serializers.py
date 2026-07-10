from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(
        source='template.name',
        read_only=True,
        default=''
    )
    template_category = serializers.CharField(
        source='template.category',
        read_only=True,
        default=''
    )
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'slug',
            'status',
            'template_name',
            'template_category',
            'customisation_data',
            'preview_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'status', 'created_at', 'updated_at']

    def get_preview_url(self, obj):
        if obj.slug:
            return f"https://{obj.slug}.devlaunch.app"
        return None