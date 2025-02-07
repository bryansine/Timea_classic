from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.create_order, name='create_order'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('create-order/', views.create_order_from_cart, name='create_order_from_cart'),
    path('daraja/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('initiate-payment/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('payment-failed/',views.payment_failed, name='payment_failed'),
]



# from django.urls import path
# from . import views

# app_name = 'orders'

# urlpatterns = [
#     path('create/', views.create_order, name='create_order'),
#     path('<int:order_id>/', views.order_detail, name='order_detail'),
#     path('create-order/', views.create_order_from_cart, name='create_order_from_cart'),
#     # path('initiate-payment/', views.initiate_payment, name='initiate_payment')
#     path('initiate-payment/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
#     path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    
#     path('order/<int:order_id>/payment/', views.initiate_payment, name='initiate_payment'),
#     path('order/<int:order_id>/success/', views.payment_success, name='payment_success'),
    
#     path('daraja/callback/', views.mpesa_callback, name='mpesa_callback')
# ]
