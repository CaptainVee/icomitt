"""icomitt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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

from dj_rest_auth.views import PasswordResetConfirmView
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from dj_rest_auth.registration.views import VerifyEmailView


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

]

