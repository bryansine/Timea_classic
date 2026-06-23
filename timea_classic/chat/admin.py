# chat/admin.py
from django.contrib import admin
from .models import ChatMessage

# 1. Define your admin class layout WITHOUT the decorator at the top
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'sender', 'message_excerpt', 'timestamp')
    list_filter = ('room_name', 'timestamp', 'sender')
    search_fields = ('room_name', 'message', 'sender__username')

    def message_excerpt(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_excerpt.short_description = 'Message'


# 2. 🛡️ Safe Registration Check
# This tells Django: Only register if it hasn't been registered yet in this run!
if not admin.site.is_registered(ChatMessage):
    admin.site.register(ChatMessage, ChatMessageAdmin)