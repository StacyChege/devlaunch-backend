from rest_framework import serializers

from .models import Deployment, Project


class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deployment
        fields = ['id', 'status', 'build_log', 'is_rollback', 'created_at']
        read_only_fields = fields


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
    template_is_deployable = serializers.SerializerMethodField()
    preview_url = serializers.ReadOnlyField(source='subdomain_url')
    live_url = serializers.SerializerMethodField()
    latest_deployment = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'slug',
            'status',
            'template_name',
            'template_category',
            'template_is_deployable',
            'customisation_data',
            'preview_url',
            'live_url',
            'latest_deployment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'status', 'created_at', 'updated_at']

    def get_template_is_deployable(self, obj):
        if not obj.template:
            return False
        # Local import avoids a hard projects -> templates dependency at
        # module load time; templates already imports nothing from projects.
        from templates.rendering import has_real_source
        return has_real_source(obj.template)

    def get_live_url(self, obj):
        """The real, working URL — only once a deployment has succeeded."""
        if obj.status != Project.STATUS_DEPLOYED or not obj.site_path:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.site_path) if request else obj.site_path

    def get_latest_deployment(self, obj):
        deployment = obj.deployments.first()  # Deployment.Meta.ordering = -created_at
        return DeploymentSerializer(deployment).data if deployment else None
