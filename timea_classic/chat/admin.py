from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'sender', 'message', 'timestamp')
    list_filter = ('room_name', 'sender', 'timestamp')
    search_fields = ('message', 'room_name', 'sender__username')