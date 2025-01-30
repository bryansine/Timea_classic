# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import chat.routing

# application = ProtocolTypeRouter({
#     'http': URLRouter([]),  # Handles normal HTTP requests (optional placeholder)
#     'websocket': AuthMiddlewareStack(
#         URLRouter(chat.routing.websocket_urlpatterns)
#     ),
# })