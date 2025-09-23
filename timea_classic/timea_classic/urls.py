from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Apps URLs
    path('', include('core.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('chat/', include('chat.urls')),  
    # path('checkout/', include('checkout.urls')),
    path('orders/', include('orders.urls')),
    path('daraja/', include('daraja.urls')),
    
    # path('accounts/', include('accounts.urls')),
] 

# Serve static and media files in development only
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)