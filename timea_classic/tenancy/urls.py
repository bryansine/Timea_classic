# tenancy/urls.py
from django.urls import path
from . import views

app_name = 'tenancy'

urlpatterns = [
    path('dashboard/<slug:tenant_slug>/', views.merchant_overview, name='merchant_overview'),
    path('dashboard/<slug:tenant_slug>/orders/', views.merchant_orders, name='merchant_orders'),
    path('dashboard/<slug:tenant_slug>/chat/', views.merchant_chat_dashboard, name='merchant_chat_dashboard'),
    path('dashboard/<slug:tenant_slug>/chat/<str:room_name>/', views.merchant_chat_room, name='merchant_chat_room'),
]