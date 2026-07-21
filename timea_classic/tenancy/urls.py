
# tenancy/urls.py
from django.urls import path
from . import views

app_name = 'tenancy'

urlpatterns = [
    path('dashboard/<slug:tenant_slug>/', views.merchant_overview, name='merchant_overview'),
    path('dashboard/<slug:tenant_slug>/orders/', views.merchant_orders, name='merchant_orders'),
    
    path('dashboard/<slug:tenant_slug>/products/', views.merchant_products, name='merchant_products'),
    path('dashboard/<slug:tenant_slug>/products/add/', views.merchant_product_create, name='merchant_product_create'),
    path('dashboard/<slug:tenant_slug>/products/<int:product_id>/edit/', views.merchant_product_edit, name='merchant_product_edit'),
    path('dashboard/<slug:tenant_slug>/products/<int:product_id>/delete/', views.merchant_product_delete, name='merchant_product_delete'),
    
    path('dashboard/<slug:tenant_slug>/chat/', views.merchant_chat_dashboard, name='merchant_chat_dashboard'),
    path('dashboard/<slug:tenant_slug>/chat/<str:room_name>/', views.merchant_chat_room, name='merchant_chat_room'),
    
    path('dashboard/<slug:tenant_slug>/categories/', views.merchant_categories, name='merchant_categories'),
    path('dashboard/<slug:tenant_slug>/products/<int:product_id>/variants/', views.merchant_product_variants, name='merchant_product_variants'),
    
    path('dashboard/<slug:tenant_slug>/orders/', views.merchant_orders, name='merchant_orders'),
    path('dashboard/<slug:tenant_slug>/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
]