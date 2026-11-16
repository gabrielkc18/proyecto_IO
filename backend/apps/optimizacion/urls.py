
from rest_framework.routers import DefaultRouter

from .views import (
    EjecucionViewSet,
    ProblemaOptimizacionViewSet,
)


router = DefaultRouter()

router.register(
    r"ejecuciones",
    EjecucionViewSet,
    basename="ejecucion"
)

router.register(
    r"problemas",
    ProblemaOptimizacionViewSet,
    basename="problema-optimizacion"
)

urlpatterns = router.urls
