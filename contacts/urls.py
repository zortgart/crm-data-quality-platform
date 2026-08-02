from rest_framework.routers import DefaultRouter
from .views import ContactViewSet

router = DefaultRouter()
router.register(prefix="", viewset=ContactViewSet, basename="contact")

urlpatterns = router.urls
