from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_dashboard, name='chat_dashboard'),
    path('<str:room_name>/', views.room, name='room'), 
]