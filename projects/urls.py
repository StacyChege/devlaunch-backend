from django.urls import path
from .views import (
    ProjectDeployView,
    ProjectDeploymentListView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectLogoUploadView,
    ProjectRollbackView,
    ProjectStatsView,
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project_list_create'),
    path('stats/', ProjectStatsView.as_view(), name='project_stats'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/logo/', ProjectLogoUploadView.as_view(), name='project_logo_upload'),
    path('<int:pk>/deploy/', ProjectDeployView.as_view(), name='project_deploy'),
    path('<int:pk>/rollback/', ProjectRollbackView.as_view(), name='project_rollback'),
    path('<int:pk>/deployments/', ProjectDeploymentListView.as_view(), name='project_deployments'),
]
