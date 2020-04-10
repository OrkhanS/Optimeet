from .models import *;
from .serializers import RoomSerializer,MessageSerializer
from copy import deepcopy
from .utils import create_room
from rest_framework.exceptions import APIException
from rest_framework.views import APIView,Response
from rest_framework.pagination import PageNumberPagination,CursorPagination
from rest_framework.generics import ListAPIView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated,IsAdminUser

class MyCursorPagination(CursorPagination):
	page_size = 15
	ordering = "-id"

class CustomRoomPagination(PageNumberPagination):  
       page_size = 10

class GetRoom(APIView):
	permission_classes=[IsAuthenticated]
	def get(self,request,id):
		user = request.user
		target_user = User.objects.get(pk=id)
		if (user == target_user):
			raise APIException("Room should be between separate users")
		else:
			room_id = create_room([user, target_user])
		return Response(room_id)

class ChattedUser(ListAPIView):
	permission_classes=[IsAuthenticated]
	serializer_class = RoomSerializer
	pagination_class = CustomRoomPagination

	def get_queryset(self):
		return self.request.user.rooms.all()

class GetChat(APIView):
	def get(self,request,room_uuid):
		rm = Room.objects.get(id = room_uuid)
		s = RoomSerializer(instance=rm,context={"request":request})
		return Response(s.data)
	def delete(self,request,room_uuid):
		rm = Room.objects.get(id = room_uuid)
		if request.user in rm.members.all():
			rm.delete()
			return Response({'detail':"Deleted"},status=203)

class GetMessages(generics.ListAPIView):
	serializer_class = MessageSerializer
	permission_classes=[IsAuthenticated]
	pagination_class = MyCursorPagination
	lookup_url_kwarg = "room_uuid"
	def get_queryset(self):
		data = self.request.query_params
		assert "room_id" in data,"Please Enter Room_id"
		room_id = data["room_id"]
		room = Room.objects.get(pk=room_id)
		return Message.objects.filter(room=room)

class ReadChatsTillNow(APIView):
	permission_classes = [IsAuthenticated]
	def post(self,request):
		assert 'room_id' in request.data
		try:
			room_messages = Message.objects.filter(room=request.data['room_id'])
			room_messages = room_messages.exclude(recipients=request.user.id)
			for room_message in room_messages:
				room_message.recipients.add(request.user)
				room_message.save()
			return Response()	
		except:
			return Response(status=400)	

class ReadLastChats(APIView):
	permission_classes = [IsAuthenticated]
	def post(self,request):
		assert 'room_id' in request.data
		try:
			request = self.request
			room_count = RoomMembers.objects.filter(room_id=request.data['room_id'], user=request.user)[0]
			room_count.unread_count = 0
			room_count.save()
			return Response()	
		except:
			return Response(status=400)	
