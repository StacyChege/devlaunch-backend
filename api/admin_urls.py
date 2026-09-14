from django.urls import path

from .admin_views import (
    AdminDeploymentListView,
    AdminOverviewView,
    AdminTemplateDetailView,
    AdminTemplateListCreateView,
    AdminUserListView,
    AdminUserSetActiveView,
)

urlpatterns = [
    path('overview/', AdminOverviewView.as_view(), name='admin_overview'),
    path('users/', AdminUserListView.as_view(), name='admin_users'),
    path('users/<int:pk>/set-active/', AdminUserSetActiveView.as_view(), name='admin_user_set_active'),
    path('templates/', AdminTemplateListCreateView.as_view(), name='admin_templates'),
    path('templates/<int:pk>/', AdminTemplateDetailView.as_view(), name='admin_template_detail'),
    path('deployments/', AdminDeploymentListView.as_view(), name='admin_deployments'),
]
