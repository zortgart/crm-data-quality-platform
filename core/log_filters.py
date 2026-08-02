import logging
from threading import local

_thread_locals = local()

def set_current_request_id(request_id):
    _thread_locals.request_id = request_id

def get_current_request_id():
    return getattr(_thread_locals, 'request_id', None)

class RequestIdFilter(logging.Filter):
    """
    Adds the correlation_id to log records so the formatter can use it.
    """
    def filter(self, record):
        record.correlation_id = get_current_request_id() or 'system'
        return True
