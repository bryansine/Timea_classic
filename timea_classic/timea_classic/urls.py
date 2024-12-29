
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
    # path('checkout/', include('checkout.urls')),
    path('orders/', include('orders.urls')),
    # path('api/', include('api.urls')),
    # path('api/products/', include('api.products.urls')),    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)