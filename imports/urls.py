from rest_framework.routers import DefaultRouter
from .views import ImportJobViewSet

router = DefaultRouter()
router.register(prefix="", viewset=ImportJobViewSet, basename="import")

urlpatterns = router.urls
