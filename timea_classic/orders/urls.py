from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.create_order, name='create_order'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('create-order/', views.create_order_from_cart, name='create_order_from_cart'),
    # path('initiate-payment/', views.initiate_payment, name='initiate_payment')
    path('initiate-payment/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
]