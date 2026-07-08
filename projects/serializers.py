from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(
        source='template.name',
        read_only=True,
        default=''
    )
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'status',
            'template_name',
            'preview_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def get_preview_url(self, obj):
        return f"https://{obj.slug}.devlaunch.app" if obj.slug else None