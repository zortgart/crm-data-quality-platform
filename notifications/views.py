from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    API endpoint that allows users to view their notifications.
    """
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"status": "notification marked as read"})

    @action(detail=False, methods=['post'])
    def read_all(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        updated_count = notifications.update(is_read=True)
        return Response({"status": f"{updated_count} notifications marked as read"})
