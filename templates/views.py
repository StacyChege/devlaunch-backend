from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from .models import Template
from .serializers import TemplateSerializer


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


class TemplateDetailView(APIView):
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