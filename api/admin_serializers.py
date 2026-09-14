from django.contrib.auth import get_user_model
from rest_framework import serializers

from projects.models import Deployment
from templates.models import Template

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    project_count = serializers.IntegerField(read_only=True)
    deployed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'role',
            'is_active',
            'is_verified',
            'date_joined',
            'project_count',
            'deployed_count',
        ]
        read_only_fields = fields


class AdminSetActiveSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


class AdminTemplateSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source='get_category_display', read_only=True
    )
    project_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Template
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'category',
            'category_display',
            'tech_stack',
            'preview_url',
            'source_path',
            'thumbnail',
            'is_premium',
            'is_active',
            'created_at',
            'project_count',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'category_display', 'project_count']


class AdminDeploymentSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_slug = serializers.CharField(source='project.slug', read_only=True)
    developer_email = serializers.CharField(source='project.developer.email', read_only=True)

    class Meta:
        model = Deployment
        fields = [
            'id',
            'project_name',
            'project_slug',
            'developer_email',
            'status',
            'is_rollback',
            'created_at',
        ]
        read_only_fields = fields
