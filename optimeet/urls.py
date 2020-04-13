from django.contrib import admin
from django.urls import path,include
from django.conf.urls import url
from APP.chat_api import ChattedUser,GetRoom,GetMessages,ReadChatsTillNow,GetChat,ReadLastChats
from APP.phoneapi import Request, Verify
#from APP.fcm_notification import Send
from APP.api import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),   
    #------------------------------------------Users------------------------------------------
    url(r'api/users/$', UserList.as_view(), name='User List API'),
    url(r'api/users/(?P<id>\d+)/$', UserDetail.as_view(), name='Specific User Detail API'),
    url(r'api/auth/$', UserAuthentication.as_view(), name='User Authentication API'),
    url(r'api/users/me/$', CurrentUser.as_view(), name='Current User Details API'),
    url(r'api/logout', UserAuthentication.as_view(), name='User Log Out'),
   
    #------------------------------------------Cities------------------------------------------
    url(r'api/cities/$', CityList.as_view(), name='City List API'),
    url(r'api/countries/$', CountryList.as_view(), name="Country List"),

    #------------------------------------------Chats-------------------------------------------
    url(r'api/chats/$',ChattedUser.as_view(),name="Chatted users"),
    url(r'api/chats/(?P<room_uuid>[\w,-]+)',GetChat.as_view(),name="Chatted users"),
    url(r'api/chat/(?P<id>\d+)',GetRoom.as_view(),name="Get Chat Room"),
    url('api/chat/messages',GetMessages.as_view(),name="Get Messages Room"),
    #url('api/chat/read',ReadChatsTillNow.as_view(),name="Read all chats till now"),
    url('api/chat/readlast',ReadLastChats.as_view() ,name="Read the last messages"),

    #------------------------------------------Suggestions--------------------------------------
    url(r'api/match/', IwantToMatchSomeone.as_view(),name="Get Your Match"),
    
   
    #------------------------------------------FileUload------------------------------------------
    url(r'api/fileupload/userimage/$', ImageUploadUser.as_view(), name="Upload Image of User"),
    
    #------------------------------------------Notifications------------------------------------------
    url(r'api/readnotifications/(?P<id>\d+)/$', MarkReadNotifications.as_view(), name="Read Notification"),
    url(r'api/shownotifications/$', AllnotReadNotifications.as_view(), name="Show Not Read Notification"),
    
    #url(r'api/sendmessage/$', Send.as_view(), name="Message"),
    #------------------------------------------PhoneVerify------------------------------------------
    url(r'api/request/phone/$', Request.as_view(), name="Phone Number Upload"),
    url(r'api/verify/phone/$', Verify.as_view(), name="Phone Number Verification"),

    # ---------------------------------------EmailVerify------------------------------------------
    url(r'api/request/email/$',SendVerification.as_view(),name="Send Email Verficiation"),
    url(r'api/request/verify/$',VerfiyEmail.as_view(),name="Verify Email Verficiation")


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)