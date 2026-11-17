from django.contrib import admin
from django.urls import path, include

from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.cuentas.views import AccountTokenObtainPairView, AccountTokenRefreshView
from config.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(
            permission_classes=[AllowAny],
            authentication_classes=[],
        ),
        name="openapi-schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="openapi-schema",
            permission_classes=[AllowAny],
            authentication_classes=[],
        ),
        name="swagger-ui",
    ),

    path("api/", include("apps.cuentas.urls")),
    path("api/", include("apps.workspaces.urls")),
    path("api/", include("apps.problemas.urls")),
    path("api/", include("apps.productos.urls")),
    path("api/", include("apps.recursos.urls")),
    path("api/", include("apps.optimizacion.urls")),
    path("api/", include("apps.resultados.urls")),
    path("api/", include("apps.inteligencia_artificial.urls")),

    path(
        "api/token/",
        AccountTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        AccountTokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
