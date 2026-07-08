from rest_framework import serializers
from .models import Template


class TemplateSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

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

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None