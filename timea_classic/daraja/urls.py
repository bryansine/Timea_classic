from .views import stk_push
from django.urls import path
from .views import mpesa_token_view

app_name = 'daraja'

urlpatterns = [
    path("stk_push/", stk_push, name="stk_push"),
    path('token/', mpesa_token_view, name='mpesa_token'),
]
