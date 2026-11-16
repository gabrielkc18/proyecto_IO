
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalisisIAViewSet,
    GenerarAnalisisAPIView,
)


router = DefaultRouter()

router.register(
    r"analisis-ia",
    AnalisisIAViewSet,
    basename="analisis-ia"
)

urlpatterns = [
    path(
        "analisis-ia/ejecuciones/<int:ejecucion_id>/generar/",
        GenerarAnalisisAPIView.as_view(),
        name="generar-analisis-ia",
    ),
] + router.urls
