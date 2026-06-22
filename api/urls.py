from django.urls import path
from .views import ping_backend

urlpatterns = [
    path('ping/', ping_backend),
]