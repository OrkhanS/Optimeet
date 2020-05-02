'''AI--------------------------------------------------------------------------
    Django Imports
--------------------------------------------------------------------------AI'''
from uuid import UUID
import json
from .models import Room, Message, User, RoomMembers
import bleach
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.db import connection
from pyfcm import FCMNotification
from django.db.models import Q


'''AI--------------------------------------------------------------------------
    Third-party Imports
--------------------------------------------------------------------------AI'''


'''AI--------------------------------------------------------------------------
    App Imports
--------------------------------------------------------------------------AI'''


'''AI--------------------------------------------------------------------------
    Python Imports
--------------------------------------------------------------------------AI'''


'''
AI-------------------------------------------------------------------
    Database Access methods below
-------------------------------------------------------------------AI
'''
@database_sync_to_async
def get_room(room_id, multitenant=False, schema_name=None):
    if multitenant:
        if not schema_name:
            raise AttributeError("Multitenancy support error: \
                scope does not have multitenancy details added. \
                did you forget to add ChatterMTMiddlewareStack to your routing?")
        else:
            from django_tenants.utils import schema_context
            with schema_context(schema_name):
                return Room.objects.get(id=room_id)
    else:
        return Room.objects.get(id=room_id)


'''
AI-------------------------------------------------------------------
    1. Select the Room
    2. Select the user who sent the message
    3. Select the message to be saved
    4. Save message
    5. Set room update time to message date_modified
-------------------------------------------------------------------AI
'''
@database_sync_to_async
def save_message(room, sender, text, multitenant=False, schema_name=None):
    if multitenant:
        if not schema_name:
            raise AttributeError("Multitenancy support error: \
                scope does not have multitenancy details added. \
                did you forget to add ChatterMTMiddlewareStack to your routing?")
        else:
            from django_tenants.utils import schema_context
            with schema_context(schema_name):
                new_message = Message(room=room, sender=sender, text=text)
                new_message.save()
                new_message.recipients.add(sender)
                new_message.save()
                room.date_modified = new_message.date_modified
                room.save()
                return new_message
    else:
        new_message = Message(room=room, sender=sender, text=text)
        new_message.save()
        new_message.recipients.add(sender)
        new_message.save()
        #____________________________________________
        members = RoomMembers.objects.filter(room=room).exclude(user=sender)
        for member in members:
            if not member.online:
                member.unread_count += 1
                member.save()        
        #____________________________________________
        room.date_modified = new_message.date_modified
        room.save()
        return new_message


class ChatConsumer(AsyncJsonWebsocketConsumer):

    '''
    AI-------------------------------------------------------------------
        WebSocket methods below
    -------------------------------------------------------------------AI
    '''
    async def connect(self):
        self.user = self.scope['user']

        self.room_username_list = []  # Cache room usernames to send alerts

        self.schema_name = self.scope.get('schema_name', None)
        self.multitenant = self.scope.get('multitenant', False)
        for param in self.scope['path'].split('/'):
            try:
                room_id = UUID(param, version=4)
                break
            except ValueError:
                pass

        # Check if the user connecting to the room's websocket belongs in the room
        try:
            self.room = await get_room(room_id, self.multitenant, self.schema_name)
            if self.multitenant:
                from django_tenants.utils import schema_context
                with schema_context(self.schema_name):
                    if self.user in self.room.member_users.all():
                        self.room_group_name = 'chat_%s' % self.room.id
                        await self.channel_layer.group_add(
                            self.room_group_name,
                            self.channel_name
                        )
                        self.room.save()
                        await self.accept()

                        for user in self.room.member_users.all():
                            self.room_username_list.append(user.id)
                    else:
                        await self.disconnect(403)
            else:
                if self.user in self.room.member_users.all():
                    self.room_group_name = 'chat_%s' % self.room.id
                    await self.channel_layer.group_add(
                        self.room_group_name,
                        self.channel_name
                    )
                    # self.room.save()
                    
                    await self.accept()

                    for user in self.room.member_users.all():
                        self.room_username_list.append(user.id)
                else:
                    await self.disconnect(403)
        except Exception as ex:
            await self.disconnect(500)
            raise ex

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # self.room.save()

    async def receive_json(self, data):
        if (data['sender'] != self.user.id)\
                or data['room_id'] != str(self.room.id):
            await self.disconnect(403)

        message_type = data['message_type']
        if message_type == "text":
            message = data['message']
            room_id = data['room_id']

            # Clean code off message if message contains code
            self.message_safe = bleach.clean(message)

            # try:
            #     # room = await self.get_room(room_id)
            #     room_group_name = 'chat_%s' % room_id
            # except Exception as ex:
            #     raise ex
            #     await self.disconnect(500)

            msg = await save_message(self.room,
                                     self.user,
                                     self.message_safe,
                                     self.multitenant,
                                     self.schema_name
                                     )

            date_created = msg.date_created.strftime("%d %b %Y %H:%M:%S %Z")
            date_modified = msg.date_modified.strftime("%d %b %Y %H:%M:%S %Z")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'id': msg.id,
                    'type': 'send_to_websocket',
                    'message_type': 'text',
                    'text': self.message_safe,
                    'recipients': [self.user.id],
                    'date_created': date_created,
                    'date_modified': date_modified,
                    'sender': self.user.id,
                    'room_id': room_id,
                }
            )

            for email in self.room_username_list:
                if email != self.user.id:
                    await self.channel_layer.group_send(
                        f'user_{str(email)}',
                        {
                            'id': msg.id,
                            'type': 'receive_json',
                            'message_type': 'text',
                            'text': self.message_safe,
                            'recipients': [self.user.id],
                            'date_created': date_created,
                            'date_modified': date_modified,
                            'sender': self.user.id,
                            'room_id': room_id,
                        }
                    )
                    notifyUser = User.objects.get(pk=email)
                    member = RoomMembers.objects.get(room=room_id, user=notifyUser)
                    if member.userAccess == True:
                        if notifyUser.deviceToken != 'None' or notifyUser.deviceToken != '':
                            push_service = FCMNotification(
                                api_key="AAAAinQp9PE:APA91bEZ0S6YENxW0N9D4b2CVF_GYSrM4rRp_BvDnSxdQOvwLy30DlHb8AhXXF7YEpPT07r5FDIYo0ek3m-p0gGMBzB9o8bH08MiKX7D7NxhHtGp6oVEt2uX8XStfPKwRdrl7kamgOl9")
                            registration_id = notifyUser.deviceToken
                            message_title = self.user.first_name
                            message_body = self.message_safe
                            data = {
                                "id": msg.id,
                                "text": message_body,
                                "sender": self.user.id,
                                "date_modified": date_modified,
                                "room_id":room_id
                            }
                            push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body, data_message=data, content_available=True)

    async def send_to_websocket(self, event):
        await self.send_json(event)


class AlertConsumer(AsyncJsonWebsocketConsumer):
    '''
    AI-------------------------------------------------------------------
        WebSocket methods below
    -------------------------------------------------------------------AI
    '''
    async def connect(self):
        self.user = self.scope['user']
        self.user.set_online()
        self.user_group_name = f'user_{str(self.user.id)}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        self.user = self.scope['user']
        self.user.set_offline()
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def receive_json(self, data):

        # Check if the data has been sent to this consumer by the currently
        # logged in user

        data['type'] = 'send_to_websocket'
        await self.channel_layer.group_send(self.user_group_name, data)

    async def send_to_websocket(self, event):
        await self.send_json(event)
