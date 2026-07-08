from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Project
from .serializers import ProjectSerializer

try:
    from templates.models import Template
except ImportError:
    Template = None


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
        serializer = ProjectSerializer(projects, many=True)
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

        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            project = Project.objects.get(id=pk, developer=request.user)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProjectSerializer(project)
        return Response(serializer.data)