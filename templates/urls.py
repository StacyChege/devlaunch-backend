from django.urls import path
from .views import TemplateListView, TemplateDetailView, TemplatePreviewView

urlpatterns = [
    path('', TemplateListView.as_view()),
    path('<slug:slug>/preview/', TemplatePreviewView.as_view(), name='template_preview'),
    path('<slug:slug>/', TemplateDetailView.as_view()),
]
