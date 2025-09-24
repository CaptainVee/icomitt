"""icomitt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Icommit",
        default_version="v1",
        description="API endpoints for Icommit",
        contact=openapi.Contact(email="captainvee3@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0)),
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/v1/auth/', include('core_apps.users.urls')),
    path('api/v1/goals/', include('core_apps.goals.urls')),
    path('api/v1/wallet/', include('core_apps.wallets.urls')),
    # path('api/v1/verify/', include('core_apps.verifications.urls')),
    path('api/v1/logs/', include('core_apps.logs.urls')),

]

