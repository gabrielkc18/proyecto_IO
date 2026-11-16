
from rest_framework.routers import DefaultRouter

from .views import (
    ResultadoProductoViewSet,
    ResultadoRecursoViewSet
)


router = DefaultRouter()

router.register(
    r"resultados-productos",
    ResultadoProductoViewSet,
    basename="resultado-producto"
)

router.register(
    r"resultados-recursos",
    ResultadoRecursoViewSet,
    basename="resultado-recurso"
)

urlpatterns = router.urls
