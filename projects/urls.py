from django.urls import path
from .views import ProjectLogoUploadView, ProjectStatsView, ProjectDetailView

urlpatterns = [
    path('stats/', ProjectStatsView.as_view()),
    path('<int:pk>/', ProjectDetailView.as_view()),
    path('<int:pk>/logo/', ProjectLogoUploadView.as_view(), name='project_logo_upload'),
]