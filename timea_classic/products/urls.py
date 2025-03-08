from . import views
from django.urls import path


app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('<int:product_id>/', views.product_detail, name='detail'),
    path('category/<int:category_id>/', views.product_by_category, name='category'),
    path('search/', views.product_search, name='search'),
    path('cart/add_variant/<int:product_id>/<int:variant_id>/', views.add_variant_to_cart, name='add_variant'),
]
