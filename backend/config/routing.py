"""
Routing WebSocket pour PRESSO
"""
from django.urls import re_path
from apps.core.consumers import NotificationConsumer

websocket_urlpatterns = [
    # WebSocket pour les notifications en temps réel
    # ws://localhost:8000/ws/notifications/<user_id>/
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', NotificationConsumer.as_asgi()),
]

