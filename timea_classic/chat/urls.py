from . import views
from django.urls import path

urlpatterns = [
    path('chat/<str:room_name>/', views.room, name='room'),
]