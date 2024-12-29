from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('add/<int:product_id>/', views.add_to_cart, name='add'),
    path('add_variant/<int:product_id>/<int:variant_id>/', views.add_to_cart, name='add_variant'),
    path('view/', views.view_cart, name='view'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove'),
    # path('create-order/', views.create_order_from_cart, name='create_order_from_cart'),
    
    # path('checkout/', views.checkout, name='checkout'),
    # path('order_complete/', views.order_complete, name='order_complete'),
    # path('order_cancelled/', views.order_cancelled, name='order_cancelled'),
    # path('order_history/', views.order_history, name='order_history'),
]