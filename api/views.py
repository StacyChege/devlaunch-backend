from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from .serializers import RegisterSerializer, UserSerializer, ProjectSerializer, TemplateSerializer
from .models import Project, Template

try:
    from .models import Template
except ImportError:
    Template = None  # Handle the case where Template model is not defined

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    

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

class TemplateListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Template.objects.filter(is_active=True)

        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category.upper())

        templates = queryset.order_by('name')
        serializer = TemplateSerializer(
            templates,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
class TemplateDetailView(APIView):  # 👈 Make sure this line matches exactly!
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            template = Template.objects.get(slug=slug, is_active=True)
        except Template.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = TemplateSerializer(
            template,
            context={'request': request}
        )
        return Response(serializer.data)