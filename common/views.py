# =============================================================
# common/views.py — Health & Readiness Endpoints
# =============================================================
#
# WHY health checks?
#   Load balancers, orchestrators (k8s), and monitoring tools need
#   a way to know if the application is alive and ready to serve traffic.
#
# LIVENESS  (/health/)  — "Is the process alive?"
#   Returns 200 if Django can handle a request.
#   If this fails, the process is dead → restart it.
#
# READINESS (/ready/)   — "Is the app ready to serve traffic?"
#   Returns 200 only if all DEPENDENCIES are healthy.
#   Phase 1: Verifies PostgreSQL connection.
#   Phase 8: Will also verify Redis.
#   If this fails, take the instance out of the load balancer pool
#   but don't restart it (it might just be waiting for DB).
#
# Java/Spring Boot equivalent:
#   Spring Boot Actuator: /actuator/health, /actuator/info
#   Liveness: management.endpoint.health.probes.enabled=true
# =============================================================

import logging

from django.db import connection, OperationalError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Liveness check.

    Returns 200 if the Django application is running.
    This endpoint must be extremely fast — no DB calls.

    GET /health/
    Response: {"status": "ok", "service": "crm-data-quality-platform"}
    """
    return Response(
        {
            "status": "ok",
            "service": "crm-data-quality-platform",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check.

    Returns 200 only when ALL required dependencies are healthy.
    Currently checks: PostgreSQL.
    Phase 8 will also check: Redis.

    GET /ready/
    Response (healthy):   {"status": "ready",    "checks": {"database": "ok"}}
    Response (unhealthy): {"status": "not_ready", "checks": {"database": "error: ..."}}
    """
    checks = {}
    overall_healthy = True

    # ----------------------------------------------------------
    # Database check
    # Execute the lightest possible query: SELECT 1
    # This verifies:
    #   1. Django can acquire a connection from the pool
    #   2. PostgreSQL is running and accepting connections
    #   3. The application user has at least SELECT permission
    # ----------------------------------------------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
        logger.debug("Readiness check: database OK")
    except OperationalError as e:
        checks["database"] = f"error: {str(e)}"
        overall_healthy = False
        logger.error("Readiness check: database FAILED — %s", str(e))

    # Phase 8: Redis check will be added here
    # try:
    #     from django.core.cache import cache
    #     cache.set("_readiness_check", "1", timeout=5)
    #     checks["redis"] = "ok"
    # except Exception as e:
    #     checks["redis"] = f"error: {str(e)}"
    #     overall_healthy = False

    http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return Response(
        {
            "status": "ready" if overall_healthy else "not_ready",
            "checks": checks,
        },
        status=http_status,
    )
