from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/", include("apps.workspaces.urls")),
    path("api/", include("apps.problemas.urls")),
    path("api/", include("apps.productos.urls")),
    path("api/", include("apps.recursos.urls")),
    path("api/", include("apps.optimizacion.urls")),
    path("api/", include("apps.resultados.urls")),
    path("api/", include("apps.inteligencia_artificial.urls")),

    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
