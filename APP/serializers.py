from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.exceptions import ValidationError 
from .models import *

class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)    
    class Meta:
        model = User
        fields = ('id','email','is_active','is_staff', 'rating', 'is_number_verified','is_email_verified','is_photo_verified','password','password2','avatarpic','deviceToken',"online","last_online", 'language1','language2','gender')
        extra_kwargs = {
            'password':{'write_only':True}
        }
    
    def save(self):
        account = User(
            email=self.validated_data['email'],
            is_staff=True,
            is_superuser=True,
        )
        password = self.validated_data['password']
        password2 = self.validated_data['password2']
        language1 = self.validated_data['language1']
        language2 = self.validated_data['language2']
        gender = self.validated_data['gender']
        deviceToken = self.validated_data['deviceToken']

        if password!=password2:
            raise serializers.ValidationError({'password':'Passwords do not match'})
        account.set_password(password)
        account.save()
        return account


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Posts
        fields = ("id","ownerPost","content","date", "lang")

class MinimalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id","email","is_number_verified","is_email_verified","hasMatchedToday","is_photo_verified",'last_login','rating','avatarpic',"last_online",'online', 'language1','language2','gender')
        read_only_fields = ("id","email","is_number_verified","is_email_verified","is_photo_verified",'last_login','rating','avatarpic',"last_online",'online')

class MatchByLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matches
        fields = ("id","date_created")


class NotificationsSerializer(serializers.ModelSerializer):
    owner = MinimalUserSerializer(read_only=True)
    class Meta:
        model = Notification
        fields = ("id", "owner", "date", "content")
        read_only_fields = ("id", "owner")
        

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BriddgyCities
        fields = ['city_ascii', 'country', 'id']
        read_only_fields = ['city_ascii', 'country', 'id']

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BriddgyCities
        fields = ['country', 'id']
        read_only_fields = ['country', 'id']


class PicturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pictures
        fields = ['id','image', 'owner', 'object_id', 'content_type']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        exclude = ["room"]
class RoomMembersSerializer (serializers.ModelSerializer):
    user = MinimalUserSerializer(read_only=True)
    class Meta:
        model = RoomMembers
        fields = "__all__"

class RoomSerializer(serializers.ModelSerializer):
    members = RoomMembersSerializer(many=True)    
    class Meta:
        model = Room
        fields = ("id","date_created","date_modified","members")
    # def __indexOf(self,array):
    #     for num,item in enumerate(array):
    #         if item['user']['id'] == self.context['request'].user.id:
    #             return num
    #     return -1

    # def to_representation(self,instance):
    #     data=super(RoomSerializer,self).to_representation(instance)

    #     index = self.__indexOf(data['members'])
    #     if index >=0:
    #         del data['members'][index]             
    #     return data   







