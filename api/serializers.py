from rest_framework import serializers
from django.contrib.auth import get_user_model

from api.models import Project, Template

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role']

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


class TemplateSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)

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
            'thumbnail_url',
            'is_premium',
            'is_active',
            'created_at',
        ]

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None
