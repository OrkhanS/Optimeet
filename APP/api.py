from django.core.mail import send_mail
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from .serializers import *
from .models import *
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import filters, generics
from datetime import datetime
from pprint import pprint
from django.db.models import F, Sum, FloatField, Avg
from django.db.models import Q
from PIL import Image
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
import json
from django import db
from random import randint

#---------------------------------------------------------------------Users---------------------------------------------------------------------
class UserAuthentication(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if request.data["deviceToken"] != '':
            user.deviceToken = request.data["deviceToken"]
        token, created = Token.objects.get_or_create(user=user)
        if(not created):
            user.last_login = datetime.now()
            user.save()
        return Response(token.key)
    def patch(self, request):
        user = Token.objects.get(key=request.data['token']).user
        user.deviceToken = "None"
        user.save()
        return Response(status=status.HTTP_200_OK)

@permission_classes((AllowAny, ))
class UserList(generics.ListAPIView, APIView):
    queryset = User.objects.all()
    serializer_class = MinimalUserSerializer
    def post(self, request):
        newData = {
            "email":request.data["email"],
            "gender": request.data['gender'],
            "language1":request.data['language1'],
            "language2":request.data['language2'],
            "password":request.data['password'],
            "password2":request.data['password2'],
            "wantstoMatch":True
        }
        serializer = UserSerializer(data=newData)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, "detail":serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@permission_classes((AllowAny, ))
class UserDetail(APIView):
    def getUserInfo(self, id):
        try:
            model = User.objects.get(id=id)
            return model
        except User.DoesNotExist:
            return

    def get(self, request, id):
        if not self.getUserInfo(id):
            return Response('User Not Found', status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(self.getUserInfo(id))
        return Response(serializer.data)

    def put(self, request, id):
        request = self.request
        if request.user.is_authenticated:
            if not self.getUserInfo(id):
                return Response('User Not Found', status=status.HTTP_404_NOT_FOUND)
            serializer = UserSerializer(self.getUserInfo(id), data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        request = self.request
        if request.user.is_authenticated:
            if not self.getUserInfo(self.kwargs.get("id")):
                return Response('User Not Found', status=status.HTTP_404_NOT_FOUND)
            User.objects.get(id=self.kwargs.get("id")).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response('Error!', status=status.HTTP_400_BAD_REQUEST)

class CurrentUser(APIView):
    def get(self, request):
        serializer = MinimalUserSerializer(User.objects.get(id=request.user.id))
        return Response(serializer.data)

#-------------------------------------------------------------------POSTS------------------------------------------------------------------
@permission_classes((AllowAny, ))
class PostList(generics.ListAPIView, APIView):
    queryset = Posts.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        model = Posts.objects.all().order_by("-id")
        request = self.request
        lang1 = request.GET.get("lang1",None)
        lang2 = request.GET.get("lang2",None)
        if lang1:
            model=model.filter(lang=lang1)
            if request.user.is_authenticated:
                model=model.exclude(ownerPost=request.user.id)
        if lang2:
            model2 = Posts.objects.all().order_by("-id")
            model2=model2.filter(lang=lang2)
            if request.user.is_authenticated:
                model2=model2.exclude(ownerPost=request.user.id)
            model = list(model)+list(model2)

        return model

    def post(self, request):
        newData = {
            "ownerPost":request.user.id,
            "content":request.data['content'],
            "lang": request.data['lang']
        }
        serializer = PostSerializer(data=newData)
        if serializer.is_valid():
            post = serializer.save(ownerPost=request.user)
            post.ownerPost=request.user
            post.content = request.data['content'] 
            post.lang = request.data['lang'] 
            post.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, id):
    #     request = self.request
    #     if request.user.is_authenticated:
    #         postToDelete = Posts.objects.get(id=id)
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     return Response('Error!', status=status.HTTP_400_BAD_REQUEST)

class PostsOfCurrentUser(generics.ListAPIView):
    serializer_class = PostSerializer
    def get_queryset(self):
        request = self.request
        model = Posts.objects.filter(ownerPost=request.user.id).order_by("-id")
        return model


#-------------------------------------------------------------------RANDOM-------------------------------------------------------------------
class IwantToMatchSomeone(APIView):
    def get(self, request):
        # if user has already matched today, say else forbidden
        if request.user.hasMatchedToday == False:
            request = self.request
            id = request.user.id
            me = MinimalUserSerializer(User.objects.get(pk=id))
            # get users' languages
            languages = []
            languages.append(me["language1"].value)
            languages.append(me["language2"].value)

            if languages[1] != "false":
                users = User.objects.filter( Q(language1 = languages[0]) | Q(language2 = languages[0]) | Q(language1 = languages[1]) | Q(language2 = languages[1]) ).exclude(pk=request.user.id)
            else:
                users = User.objects.filter( Q(language1 = languages[0]) | Q(language2 = languages[0]) ).exclude(pk=request.user.id)
            users = users.exclude(wantstoMatch = False)
            # exclude current user and who doesn't want to match
            userList = list(users)
            count = len(userList)
            flag = 1
            hasMatched = False
            serializer = MinimalUserSerializer(userList, many=True)

            #loop throug the list of users
            while(flag == 1):
                #if there is no user that I can match then make my wantstoMatch field True
                if len(userList) == 0:
                    userNow = User.objects.get(pk = request.user.id)
                    userNow.wantstoMatch = True
                    return Response(status=status.HTTP_204_NO_CONTENT)
                count = len(userList)
                random = randint(0, count - 1)
                hasMatched = False
                hasMatched = Matches.objects.filter(user1 = request.user, user2 = userList[random]).exists() or Matches.objects.filter(user1 = userList[random], user2 = request.user).exists()
                
                #if user already matched with some user then remove him from list
                if hasMatched:
                    userList.remove(userList[random])
                # if user hasn't watched with him and he hasn't matched with anyone today
                if not hasMatched and userList[random].hasMatchedToday == False:
                    flag = 0
                    random_object = userList[random]
                    Matches.objects.create(user1 = request.user, user2 = random_object)    
                    serializer = MinimalUserSerializer(random_object)
                    user1 = User.objects.get(pk = request.user.id)
                    user2 = User.objects.get(pk = userList[random].id)
                    user1.hasMatchedToday = True
                    user1.wantstoMatch = False
                    user2.wantstoMatch = False
                    user2.hasMatchedToday = True
                    user1.save()
                    user2.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"data":"There is a problem, please wait"}, status=status.HTTP_204_NO_CONTENT)

        else:
            Response(status=status.HTTP_403_FORBIDDEN)
    # to say I don't want to match today
    def delete(self, request, id):
        request = self.request
        id = request.user.id
        user=User.objects.get(id=id)
        user.wantstoMatch = False
        return Response(status=status.HTTP_204_NO_CONTENT)

# class MatchAlgorithmByLanguage(APIView):
#     def get(self, request):
#         # Get user's languages
#         if request.user.hasMatchedToday == False:
#             request = self.request
#             id = request.user.id
#             me = MinimalUserSerializer(User.objects.get(pk=id))
#             languages = []
#             languages.append(me["language1"].value)
#             languages.append(me["language2"].value)
#             # languages.append(me.language3)
#             # languages.append(me.language4)

#             if languages[1] != "false":
#                 users = User.objects.filter( Q(language1 = languages[0]) | Q(language2 = languages[0]) | Q(language1 = languages[1]) | Q(language2 = languages[1]) ).exclude(pk=request.user.id)
#             else:
#                 users = User.objects.filter( Q(language1 = languages[0]) | Q(language2 = languages[0]) ).exclude(pk=request.user.id)
#             userList = list(users) 
#             count = len(userList)
#             flag = 1
#             hasMatched = False
#             serializer = MinimalUserSerializer(userList, many=True)

#             while(flag == 1):
#                 if len(userList) == 0:
#                     return Response(status=status.HTTP_204_NO_CONTENT)
#                 count = len(userList)
#                 random = randint(0, count - 1)
#                 hasMatched = False
#                 hasMatched = Matches.objects.filter(user1 = request.user, user2 = userList[random]).exists() or Matches.objects.filter(user1 = userList[random], user2 = request.user).exists()
#                 if hasMatched:
#                     userList.remove(userList[random])
#                 if not hasMatched and userList[random].hasMatchedToday == False:
#                     flag = 0
#                     random_object = userList[random]
#                     Matches.objects.create(user1 = request.user, user2 = random_object)    
#                     serializer = MinimalUserSerializer(random_object)
#                     user1 = User.objects.get(pk = request.user.id)
#                     user2 = User.objects.get(pk = userList[random].id)
#                     user1.hasMatchedToday = True
#                     user2.hasMatchedToday = True
#                     user1.save()
#                     user2.save()
#                     return Response(serializer.data, status=status.HTTP_200_OK)
#             return Response({"data":"There is a problem, please wait"}, status=status.HTTP_204_NO_CONTENT)
#         else:
#             return Response({"data":"You have already matched today"}, status=status.HTTP_400_BAD_REQUEST)

class AfterSeeingAdsRematch(APIView):
    def get(self, request):
        try:
            request = self.request
            user = User.objects.get(pk = request.user.id)
            user.hasMatchedToday = False
            user.save()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

#----------------------------------------------------------------Show Messages After Pay---------------------------------------------------------------------
class CloseUsersAccessToRoom(APIView):
    def get(self, request, room_id):
        try:
            request = self.request
            member = RoomMembers.objects.get(room=room_id, user = request.user)
            member.hasMatchedToday = False
            member.save()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class OpenUsersAccessToRoom(APIView):
    def get(self, request, room_id):
        try:
            request = self.request
            member = RoomMembers.objects.get(room=room_id, user = request.user)
            member.hasMatchedToday = True
            member.save()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

#---------------------------------------------------------------------Cities---------------------------------------------------------------------
@permission_classes((AllowAny, ))
class CityList(generics.ListAPIView): 
        queryset = BriddgyCities.objects.all()
        serializer_class = CitySerializer
        pagination_class = PageNumberPagination
        filter_backends = [filters.SearchFilter]
        search_fields = ['^city_ascii','=country']

@permission_classes((AllowAny, ))
class CountryList(generics.ListAPIView):
        serializer_class = CountrySerializer
        pagination_class = PageNumberPagination
        filter_backends = [filters.SearchFilter]
        search_fields = ['^country']
        def get_queryset(self):
            return BriddgyCities.objects.values("country").distinct()


#---------------------------------------------------------------------FileUpload---------------------------------------------------------------------
class ImageUploadUser(APIView):
    queryset = Pictures.objects.all()
    serializer_class = PicturesSerializer
    
    def put(self, request):
        try:
            file = request.data['file']
        except KeyError:
            return Response({"detail":"Request has no resource file attached"})
        try:
            img = Image.open(file)
            img.verify()
        except:
            raise ParseError({"detail":"Uh-Oh you can only upload images."})
        product = Pictures.objects.create(image=file, owner=request.user)
        return Response({"name": product.image.name}, status=status.HTTP_201_CREATED)

#---------------------------------------------------------------------Notifications---------------------------------------------------------------------
class MarkReadNotifications(APIView):
    def get(self, request,id):
        model=Notification.objects.get(owner=request.user,pk=id)
        model.read = True
        model.save()
        return Response({"detail":"changed"})

class AllnotReadNotifications(generics.ListAPIView):
    serializer_class = NotificationsSerializer
    def get_queryset(self):
        request = self.request
        model = Notification.objects.filter(owner=request.user, read=False)
        return model

class SendVerification(APIView):
    def get(self,request):
        user = request.user
        try:
            send_mail("Briddgy Email Confirmation",'Use %s to confirm your email' % user.confirmation_key,"q.rustam@code.edu.az",[user.email])        
            return Response({"detail":"Success"})
        except:
            return Response({"detail":"Failed to send email"},status=400)            

class VerfiyEmail(APIView):
    def post(self,request):
        key = request.data['key']
        user = request.user
        try:
            user.confirm_email(key)
            user.is_email_verified = True
            user.save()
            return Response({"detail":"Success"})
        except:
            return Response({"detail":"Incorrect Confirmation Key"},status=400)  