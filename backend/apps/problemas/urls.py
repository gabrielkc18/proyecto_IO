
from rest_framework.routers import DefaultRouter

from .views import ProblemaViewSet


router = DefaultRouter()
router.register(
    r"problemas",
    ProblemaViewSet,
    basename="problema"
)

urlpatterns = router.urls
