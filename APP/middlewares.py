from django.db import close_old_connections
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
from rest_framework.authtoken.models import Token
 
class TokenAuthMiddleware:
    """
    Custom token auth middleware
    """
 
    def __init__(self, inner):
        # Store the ASGI application we were passed
        self.inner = inner
 
    def __call__(self, scope):
 
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()
 
        # Get the token
        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
       
        # Try to authenticate the user
        try:
            # Get the User information
            obj = Token.objects.get(key=token)
            user = obj.user
            return self.inner(dict(scope, user=user))
        except:
            # Token is invalid            
            return None       
        