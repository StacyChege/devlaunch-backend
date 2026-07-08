from django.urls import path
from .views import ProjectStatsView

urlpatterns = [
    path('stats/', ProjectStatsView.as_view()),
]