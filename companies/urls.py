# =============================================================
# companies/urls.py — Company URL patterns
# =============================================================
# Router automatically generates all 6 URLs from the ViewSet.
# Java equivalent: @RestController class-level @RequestMapping

from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet

router = DefaultRouter()
# prefix="": URL will be /api/v1/companies/ (prefix added in api_urls.py)
router.register(prefix="", viewset=CompanyViewSet, basename="company")

urlpatterns = router.urls
