import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from templates.models import Template

from .deployment import run_deploy, run_rollback
from .models import Deployment, Project
from .serializers import DeploymentSerializer, ProjectSerializer


class ProjectStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        developer = request.user
        total_projects = Project.objects.filter(developer=developer).count()
        deployed_sites = Project.objects.filter(
            developer=developer,
            status=Project.STATUS_DEPLOYED
        ).count()
        recent_projects = list(
            Project.objects.filter(developer=developer)
            .order_by('-updated_at')[:5]
            .values('id', 'name', 'status', 'updated_at')
        )
        return Response({
            'total_projects': total_projects,
            'deployed_sites': deployed_sites,
            'active_domains': 0,
            'total_paid': 0,
            'recent_projects': recent_projects,
        })


class ProjectListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = Project.objects.filter(
            developer=request.user
        ).order_by('-updated_at')
        serializer = ProjectSerializer(
            projects, many=True, context={'request': request}
        )
        return Response(serializer.data)

    def post(self, request):
        template_id = request.data.get('template_id')

        if not template_id:
            return Response(
                {'error': 'template_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            template = Template.objects.get(id=template_id, is_active=True)
        except Template.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        project = Project.objects.create(
            developer=request.user,
            template=template,
            name=f"My {template.name}",
        )

        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Project.objects.get(id=pk, developer=user)
        except Project.DoesNotExist:
            return None

    def get(self, request, pk):
        project = self.get_object(pk, request.user)
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, pk):
        project = self.get_object(pk, request.user)
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProjectSerializer(
            project,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        project = self.get_object(pk, request.user)
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectLogoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            project = Project.objects.get(id=pk, developer=request.user)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        logo_file = request.FILES.get('logo')
        if not logo_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowed_types = ['image/png', 'image/svg+xml', 'image/jpeg']
        if logo_file.content_type not in allowed_types:
            return Response(
                {'error': 'Only PNG, SVG, and JPG files are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if logo_file.size > 2 * 1024 * 1024:
            return Response(
                {'error': 'File size must be under 2MB'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_extension = os.path.splitext(logo_file.name)[1]
        file_path = f"projects/{project.id}/logo{file_extension}"
        saved_path = default_storage.save(file_path, ContentFile(logo_file.read()))

        logo_url = request.build_absolute_uri(
            f"/media/{saved_path}"
        )

        customisation = project.customisation_data or {}
        customisation['logo_url'] = logo_url
        project.customisation_data = customisation
        project.save()

        return Response({'logo_url': logo_url})


class ProjectDeployView(APIView):
    """POST triggers a build. Also how redeploy works — every call renders
    the project's current customisation_data as a fresh Deployment."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            project = Project.objects.get(id=pk, developer=request.user)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND
            )

        deployment = run_deploy(project)
        serializer = DeploymentSerializer(deployment)
        http_status = (
            status.HTTP_201_CREATED
            if deployment.status == Deployment.STATUS_SUCCESS
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(
            {
                'deployment': serializer.data,
                'project': ProjectSerializer(project, context={'request': request}).data,
            },
            status=http_status,
        )


class ProjectRollbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            project = Project.objects.get(id=pk, developer=request.user)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            deployment = run_rollback(project)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DeploymentSerializer(deployment)
        return Response({
            'deployment': serializer.data,
            'project': ProjectSerializer(project, context={'request': request}).data,
        })


class ProjectDeploymentListView(APIView):
    """Deployment history for the project's dashboard (PRD F3 rollback UI)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            project = Project.objects.get(id=pk, developer=request.user)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND
            )
        deployments = project.deployments.all()  # Meta.ordering = -created_at
        return Response(DeploymentSerializer(deployments, many=True).data)


class SiteView(APIView):
    """Serves a deployed project's rendered site. Public — this *is* the
    live website. Reached today via /sites/<slug>/; once wildcard DNS for
    *.devlaunch.app points here, the same content will answer on the
    subdomain too (see DEPLOY.md)."""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            project = Project.objects.get(slug=slug)
        except Project.DoesNotExist:
            return HttpResponse('Site not found.', status=404, content_type='text/plain')

        deployment = project.deployments.filter(status=Deployment.STATUS_SUCCESS).first()
        if not deployment:
            return HttpResponse(
                'This project has not been deployed yet.',
                status=404,
                content_type='text/plain',
            )

        return HttpResponse(deployment.html, content_type='text/html')
