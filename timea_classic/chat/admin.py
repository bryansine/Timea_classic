from django.contrib import admin
from .models import ChatMessage

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'sender', 'message_excerpt', 'timestamp')
    list_filter = ('room_name', 'timestamp', 'sender')
    search_fields = ('room_name', 'message', 'sender__username')

    def message_excerpt(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_excerpt.short_description = 'Message'

if not admin.site.is_registered(ChatMessage):
    admin.site.register(ChatMessage, ChatMessageAdmin)