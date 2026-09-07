from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from .models import Template
from .serializers import TemplateSerializer

TRUE_VALUES = {'1', 'true', 'yes', 'premium'}
FALSE_VALUES = {'0', 'false', 'no', 'free'}


class TemplateListView(APIView):
    """Public template gallery with category / tech-stack / pricing filters
    and full-text search over name and description (PRD F1)."""
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Template.objects.filter(is_active=True)
        params = request.query_params

        category = params.get('category')
        if category and category.upper() != 'ALL':
            queryset = queryset.filter(category=category.upper())

        tech_stack = params.get('tech_stack')
        if tech_stack and tech_stack.upper() != 'ALL':
            queryset = queryset.filter(tech_stack__icontains=tech_stack)

        pricing = params.get('pricing') or params.get('is_premium')
        if pricing:
            value = pricing.strip().lower()
            if value in TRUE_VALUES:
                queryset = queryset.filter(is_premium=True)
            elif value in FALSE_VALUES:
                queryset = queryset.filter(is_premium=False)

        search = (params.get('search') or params.get('q') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        templates = queryset.order_by('name')
        serializer = TemplateSerializer(
            templates, many=True, context={'request': request}
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
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TemplateSerializer(template, context={'request': request})
        return Response(serializer.data)
