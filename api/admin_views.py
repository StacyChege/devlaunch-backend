"""Platform admin endpoints (PRD F6). All require the ADMIN role.

Developer oversight, template library management, and (now that F3
exists) a read-only view across all deployments. Billing lands with F5.
"""
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.models import Deployment, Project
from templates.models import Template

from .admin_serializers import (
    AdminDeploymentSerializer,
    AdminSetActiveSerializer,
    AdminTemplateSerializer,
    AdminUserSerializer,
)
from .permissions import IsAdminRole

User = get_user_model()

_DEPLOYED = Project.STATUS_DEPLOYED


class AdminBase(APIView):
    permission_classes = [IsAdminRole]


class AdminOverviewView(AdminBase):
    def get(self, request):
        users = User.objects.all()
        projects = Project.objects.all()
        templates = Template.objects.all()
        return Response({
            'total_users': users.count(),
            'developers': users.filter(role=User.DEVELOPER).count(),
            'admins': users.filter(role=User.ADMIN).count(),
            'verified_users': users.filter(is_verified=True).count(),
            'suspended_users': users.filter(is_active=False).count(),
            'total_projects': projects.count(),
            'deployed_projects': projects.filter(status=_DEPLOYED).count(),
            'total_templates': templates.count(),
            'active_templates': templates.filter(is_active=True).count(),
            'total_deployments': Deployment.objects.count(),
            'failed_deployments': Deployment.objects.filter(
                status=Deployment.STATUS_FAILED
            ).count(),
        })


class AdminUserListView(AdminBase):
    def get(self, request):
        qs = User.objects.annotate(
            project_count=Count('projects', distinct=True),
            deployed_count=Count(
                'projects', filter=Q(projects__status=_DEPLOYED), distinct=True
            ),
        ).order_by('-date_joined')

        search = (request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search) | Q(full_name__icontains=search)
            )

        role = request.query_params.get('role')
        if role:
            qs = qs.filter(role=role.upper())

        return Response(AdminUserSerializer(qs, many=True).data)


class AdminUserSetActiveView(AdminBase):
    """Suspend or reactivate a developer account."""

    def post(self, request, pk):
        try:
            target = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if target == request.user:
            return Response(
                {'error': 'You cannot change your own account status.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if target.role == User.ADMIN:
            return Response(
                {'error': 'Admin accounts cannot be suspended from here.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminSetActiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target.is_active = serializer.validated_data['is_active']
        target.save(update_fields=['is_active'])

        return Response(
            AdminUserSerializer(
                User.objects.annotate(
                    project_count=Count('projects', distinct=True),
                    deployed_count=Count(
                        'projects',
                        filter=Q(projects__status=_DEPLOYED),
                        distinct=True,
                    ),
                ).get(pk=target.pk)
            ).data
        )


def _templates_with_counts():
    return Template.objects.annotate(
        project_count=Count('projects', distinct=True)
    ).order_by('name')


class AdminTemplateListCreateView(AdminBase):
    def get(self, request):
        # Admin sees inactive templates too.
        return Response(
            AdminTemplateSerializer(_templates_with_counts(), many=True).data
        )

    def post(self, request):
        serializer = AdminTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminTemplateDetailView(AdminBase):
    def get_object(self, pk):
        return _templates_with_counts().filter(pk=pk).first()

    def get(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminTemplateSerializer(template).data)

    def patch(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        template = self.get_object(pk)
        if not template:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminDeploymentListView(AdminBase):
    """Every deployment across every developer (PRD F6)."""

    def get(self, request):
        qs = Deployment.objects.select_related(
            'project', 'project__developer'
        ).all()  # Deployment.Meta.ordering = -created_at

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())

        return Response(AdminDeploymentSerializer(qs, many=True).data)
