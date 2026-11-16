
from rest_framework.routers import DefaultRouter

from .views import RecursoViewSet, ConsumoRecursoViewSet


router = DefaultRouter()

router.register(
    r"recursos",
    RecursoViewSet,
    basename="recurso"
)

router.register(
    r"consumos",
    ConsumoRecursoViewSet,
    basename="consumo"
)

urlpatterns = router.urls
