"""
URL configuration for devlaunch_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.db import connection
from django.http import JsonResponse
from django.conf.urls.static import static
from devlaunch_backend import settings

def ping(request):
    return JsonResponse({"message": "pong", "status": "Backend is alive"})

def healthz(request):
    """Liveness + DB check for the container healthcheck."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ok', 'database': 'ok'})
    except Exception:
        return JsonResponse({'status': 'error', 'database': 'unreachable'}, status=503)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', ping, name='ping'),
    path('healthz/', healthz, name='healthz'),
    path('api/auth/', include('api.urls')),
    path('api/admin/', include('api.admin_urls')),
    path('api/projects/', include('projects.urls')),
    path('api/templates/', include('templates.urls')),
]

# Static/Media URL parsing for local asset access
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    