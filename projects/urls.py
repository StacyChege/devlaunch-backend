from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectLogoUploadView,
    ProjectStatsView,
    ProjectDetailView,
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project_list_create'),
    path('stats/', ProjectStatsView.as_view(), name='project_stats'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/logo/', ProjectLogoUploadView.as_view(), name='project_logo_upload'),
]
