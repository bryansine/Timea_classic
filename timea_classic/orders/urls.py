from . import views
from .views import buy_now
from django.urls import path

app_name = 'orders'

urlpatterns = [
    path('create/', views.create_order, name='create_order'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('create-order/', views.create_order_from_cart, name='create_order_from_cart'),
    path('daraja/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('initiate-payment/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('payment-failed/',views.payment_failed, name='payment_failed'),
    path('payment/waiting/<int:order_id>/', views.payment_waiting, name='payment_waiting'), 
    path('payment/status/<int:order_id>/', views.check_payment_status, name='check_payment_status'), 
    path("buy-now/<int:product_id>/", buy_now, name="buy_now"),

    # path('payment/waiting/<int:order_id>/', views.payment_waiting, name='payment_waiting'),
]