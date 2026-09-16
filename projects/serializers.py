import re

from rest_framework import serializers

from .models import Deployment, Domain, Project


class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deployment
        fields = ['id', 'status', 'build_log', 'is_rollback', 'created_at']
        read_only_fields = fields


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = [
            'id',
            'domain_name',
            'status',
            'record_type',
            'record_value',
            'last_check_message',
            'created_at',
            'verified_at',
            'last_checked_at',
        ]
        read_only_fields = [
            'id', 'status', 'record_type', 'record_value',
            'last_check_message', 'created_at', 'verified_at', 'last_checked_at',
        ]


# Loose but real hostname validation: labels of 1-63 chars, no leading/
# trailing hyphen, at least one dot (rejects bare TLDs and localhost).
_DOMAIN_RE = re.compile(
    r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$'
)


class AddDomainSerializer(serializers.Serializer):
    domain_name = serializers.CharField(max_length=255)

    def validate_domain_name(self, value):
        value = value.strip().lower()
        value = re.sub(r'^[a-z]+://', '', value)  # tolerate a pasted URL
        value = value.split('/')[0].split(':')[0]
        value = value.rstrip('.')

        if not _DOMAIN_RE.match(value):
            raise serializers.ValidationError(
                'Enter a valid domain, e.g. www.example.com'
            )
        if value.endswith('devlaunch.app'):
            raise serializers.ValidationError(
                'devlaunch.app subdomains are assigned automatically.'
            )
        if Domain.objects.filter(domain_name=value).exists():
            raise serializers.ValidationError(
                'This domain is already connected to a project.'
            )
        return value


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
    verified_domain = serializers.SerializerMethodField()

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
            'verified_domain',
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

    def get_verified_domain(self, obj):
        domain = obj.domains.filter(status=Domain.STATUS_VERIFIED).first()
        return domain.domain_name if domain else None
