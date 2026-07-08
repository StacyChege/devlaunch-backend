from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Project


class ProjectStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        developer = request.user

        total_projects = Project.objects.filter(developer=developer).count()

        deployed_sites = Project.objects.filter(
            developer=developer,
            status=Project.STATUS_DEPLOYED
        ).count()

        recent_projects = Project.objects.filter(
            developer=developer
        ).order_by('-updated_at')[:5].values(
            'id', 'name', 'status', 'updated_at'
        )

        return Response({
            'total_projects': total_projects,
            'deployed_sites': deployed_sites,
            'active_domains': 0,
            'total_paid': 0,
            'recent_projects': list(recent_projects),
        })