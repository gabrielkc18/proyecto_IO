
from rest_framework.routers import DefaultRouter

from .views import EjecucionViewSet


router = DefaultRouter()

router.register(
    r"ejecuciones",
    EjecucionViewSet,
    basename="ejecucion"
)

urlpatterns = router.urls
