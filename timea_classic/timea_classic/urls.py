
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #apps urls
    path('', include('core.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('chat/', include('chat.urls')),  
    # path('checkout/', include('checkout.urls')),
    path('orders/', include('orders.urls')),
    path('daraja/', include('daraja.urls')),
    
    # path('accounts/', include('accounts.urls')), #might remove this line if there is an issue with routing
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)