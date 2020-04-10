from django.urls import path

from . import consumers

websocket_urlpatterns = [
	path('ws/chatrooms/<str:room_uuid>/', consumers.ChatConsumer),
	path('ws/alert/', consumers.AlertConsumer)
]
