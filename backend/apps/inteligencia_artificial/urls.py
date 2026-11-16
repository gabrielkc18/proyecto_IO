
from rest_framework.routers import DefaultRouter

from .views import AnalisisIAViewSet


router = DefaultRouter()

router.register(
    r"analisis-ia",
    AnalisisIAViewSet,
    basename="analisis-ia"
)

urlpatterns = router.urls
