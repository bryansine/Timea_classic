import os
from decouple import config  # Import config from decouple
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import chat.routing  # Import your chat app's routing

# Use python-decouple to load the settings from the .env file
settings_module = config('DJANGO_SETTINGS_MODULE', default='timea_classic.settings')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)  # Set the environment variable for Django settings

# Application definition
application = ProtocolTypeRouter({
    # HTTP request handler
    'http': get_asgi_application(),

    # WebSocket request handler (real-time communication for the chat app)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns  # Your chat app's WebSocket URL patterns
        )
    ),
})