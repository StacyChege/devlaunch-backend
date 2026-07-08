from django.urls import path
from .views import ProjectStatsView, ProjectListCreateView, ProjectDetailView

urlpatterns = [
    path('stats/', ProjectStatsView.as_view()),
    path('', ProjectListCreateView.as_view()),
    path('<int:pk>/', ProjectDetailView.as_view()),
]