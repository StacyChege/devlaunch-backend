from rest_framework import serializers

from .models import Template
from .rendering import has_real_source


class TemplateSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    preview_url = serializers.SerializerMethodField()
    is_deployable = serializers.SerializerMethodField()

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
            'is_deployable',
            'created_at',
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    def get_is_deployable(self, obj):
        return has_real_source(obj)

    def get_preview_url(self, obj):
        """Self-rendered demo when we have real source (always current,
        never stale). Falls back to an admin-curated external URL if one
        was set — e.g. for a template hosted elsewhere before its source
        lands here. Otherwise there's honestly nothing to preview yet."""
        request = self.context.get('request')
        if has_real_source(obj):
            path = f'/api/templates/{obj.slug}/preview/'
            return request.build_absolute_uri(path) if request else path
        return obj.preview_url or None
