from django.db import models
import uuid
from django.conf import settings
from datetime import datetime
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey,GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import PermissionsMixin,UserManager
from django.utils import timezone
from simple_email_confirmation.models import SimpleEmailConfirmationUserMixin



class User(AbstractBaseUser, PermissionsMixin,SimpleEmailConfirmationUserMixin):
    is_number_verified = models.CharField(verbose_name="Is the number verified",default="false", max_length=255)
    is_email_verified = models.BooleanField(verbose_name="Is the email verified",default=False)
    is_photo_verified = models.BooleanField(verbose_name="Is the photo verified",default=False)
    hasMatchedToday = models.BooleanField(verbose_name="Has user matched today",default=False)

    first_name = models.CharField(verbose_name="first name", max_length=30, blank=False)
    last_name = models.CharField(verbose_name="last name", max_length=150, blank=False)
    email = models.EmailField(verbose_name="email address", blank=False, unique=True)
    gender = models.CharField(verbose_name="Gender",blank=False, null=False, max_length=255)
    rating = models.FloatField(verbose_name="Rating", null=True, default=0)
    language1 = models.CharField(verbose_name="First Language",blank = False,null=False,max_length=255)
    language2 = models.CharField(verbose_name="Second Language",default="false",blank = True, max_length=255)
    #language3 = models.CharField(verbose_name="Third Language",default="false", max_length=255)
    #language4 = models.CharField(verbose_name="Language 4",default="false", max_length=255)

    is_staff = models.BooleanField(
        verbose_name="staff status",
        default=False,
    )
    is_active = models.BooleanField(
        verbose_name="active",
        default=True,
       
    )
    date_joined = models.DateTimeField(verbose_name="date joined", default=timezone.now)
    online = models.BooleanField(default=False)
    last_online = models.DateTimeField(verbose_name="Last Online",default=timezone.now)
    deviceToken = models.CharField(verbose_name="Mobile Device Id", default="None", max_length=600, blank=True)
    
    objects = UserManager()
    avatar = GenericRelation("Pictures")    
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    def set_online(self):
        self.online = True        
        self.save()
        
    def set_offline(self):
        self.online = False
        self.last_online = datetime.now()
        self.save()        
    @property
    def avatarpic(self):
        s = self.avatar.all()
        if(len(s)):
            return s[len(s)-1].image.name
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email

class Matches(models.Model):
    user1 = models.ForeignKey(User, related_name="First", on_delete=models.CASCADE, null=True)
    user2 = models.ForeignKey(User, related_name="Second", on_delete=models.CASCADE, null=True)
    date_created = models.DateTimeField(auto_now_add=True) 

class BriddgyCities(models.Model):
    city = models.CharField(max_length=100)
    city_ascii = models.CharField(max_length=100)
    lat = models.FloatField(max_length=100, null=True)
    lng = models.FloatField(max_length=100, null=True)
    country = models.CharField(max_length=100, null=True)
    iso2 = models.CharField(max_length=100, null=True)
    iso3 = models.CharField(max_length=100, null=True)
    admin_name = models.CharField(max_length=100, null=True)
    capital = models.CharField(max_length=100, null=True)
    population = models.IntegerField(null=True)
    id_ofcity = models.IntegerField(null=True)
     
class Notification(models.Model):
    owner = models.OneToOneField(User, related_name="notifications",null=False, on_delete=models.CASCADE, blank=False)
    content = models.CharField(verbose_name="Address", max_length=255, default=False)
    date = models.DateField(verbose_name="date of notification")
    read = models.BooleanField(default=False)   

class EmailNotification(models.Model):
    owner = models.OneToOneField(User,related_name="email_notification",null=False,on_delete=models.CASCADE,blank=False)
    content = models.CharField(verbose_name="Address", max_length=255, default=False)
    date = models.DateField(verbose_name="date of notification")
    from_room = models.OneToOneField("Room",null=False,on_delete=models.CASCADE,blank=False)

class Messages(models.Model):
    content = models.CharField(verbose_name="Content", max_length=500)
    date = models.DateField(verbose_name="Sent")
    sentFrom = models.ForeignKey(User, related_name="SentFrom", on_delete=models.CASCADE)
    sentTo = models.ForeignKey(User, related_name="SentTo", on_delete=models.CASCADE)
    images = GenericRelation("Pictures")
    def __str__(self):
        return self.content
       
class Pictures(models.Model):
    image =  models.ImageField(verbose_name="Image")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,default=False)
    object_id = models.PositiveIntegerField(default=False)
    owner = GenericForeignKey('content_type', 'object_id')
    def __str__(self):
        return self.image.name

class DateTimeModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class RoomMembers(models.Model):
    room = models.ForeignKey("Room",related_name="members",verbose_name="Room",on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name="User",on_delete=models.CASCADE)
    userAccess = models.BooleanField(verbose_name="Can user Access to Room", default=True)     
    unread_count = models.PositiveIntegerField(default=0)
    online = models.BooleanField(default=False,verbose_name="User is online")

class Room(DateTimeModel):
    id = models.UUIDField(primary_key=True,
            default=uuid.uuid4,
            editable=False)    
    member_users = models.ManyToManyField(User,through=RoomMembers,related_name="rooms")
    def __str__(self):
        memberset = self.members.all()
        members_list = []
        for member in memberset:
            members_list.append(member.username)

        return ", ".join(members_list) 
    class Meta:
        ordering = ['-date_modified']

class Message(DateTimeModel):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, related_name='sender')
    room = models.ForeignKey(Room, on_delete=models.CASCADE,related_name="messages")
    text = models.TextField()
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL,
        related_name='recipients')
        
    def __str__(self):
        return f'{self.text} sent by "{self.sender}" in Room "{self.room}"'
    class Meta:
        ordering = ['-id']