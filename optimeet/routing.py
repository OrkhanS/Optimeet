
from channels.routing import ProtocolTypeRouter, URLRouter
import APP.routing
from APP.middlewares import TokenAuthMiddleware

application = ProtocolTypeRouter({
  'websocket': TokenAuthMiddleware(
    URLRouter(
    APP.routing.websocket_urlpatterns # send request to chatter's urls
    )
  )
})