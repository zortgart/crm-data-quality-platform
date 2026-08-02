import uuid
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog
from .log_filters import set_current_request_id

logger = logging.getLogger(__name__)


class RequestIDMiddleware(MiddlewareMixin):
    """
    Injects a UUID correlation ID into every request.
    This helps trace a single request across logs.
    """
    def process_request(self, request):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id
        set_current_request_id(request_id)

    def process_response(self, request, response):
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """
    Logs all non-safe HTTP methods (POST, PUT, PATCH, DELETE) to the AuditLog.
    """
    def process_request(self, request):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            # Read body to string for logging
            # (Note: reading request.body multiple times requires care in Django)
            if request.body:
                try:
                    request._audit_payload = json.loads(request.body.decode('utf-8'))
                except (ValueError, UnicodeDecodeError):
                    request._audit_payload = {'raw': 'binary_or_malformed'}
            else:
                request._audit_payload = None

    def process_response(self, request, response):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            user = getattr(request, 'user', None)
            if user and user.is_authenticated and hasattr(user, 'organization'):
                action = 'CREATE' if request.method == 'POST' else 'UPDATE' if request.method in ('PUT', 'PATCH') else 'DELETE'
                
                # Get IP address
                x_forwarded_for = request.headers.get('x-forwarded-for')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')

                # Log asynchronously or fire-and-forget in production.
                # Doing this synchronously for Phase 9 simplicity.
                AuditLog.objects.create(
                    organization=user.organization,
                    user=user,
                    action=action,
                    path=request.path,
                    method=request.method,
                    payload=getattr(request, '_audit_payload', None),
                    ip_address=ip
                )
        return response
