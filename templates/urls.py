from django.urls import path
from .views import TemplateListView, TemplateDetailView

urlpatterns = [
    path('', TemplateListView.as_view()),
    path('<slug:slug>/', TemplateDetailView.as_view()),
]