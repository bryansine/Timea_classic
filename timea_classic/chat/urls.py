from django.urls import path
from . import views

urlpatterns = [
    path('chat/<str:room_name>/', views.room, name='room'),
]