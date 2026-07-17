from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from .models import ChatMessage

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'sender', 'message_excerpt', 'timestamp')
    list_filter = ('room_name', 'timestamp', 'sender')
    search_fields = ('room_name', 'message', 'sender__username')

    def message_excerpt(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_excerpt.short_description = 'Message'

    # Intercept clicks on individual messages and redirect to the custom room panel
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and obj.room_name:
            # Resolves to your custom chat room view (e.g., /chat/bryan/)
            return redirect(reverse('room', kwargs={'room_name': obj.room_name}))
            
        return super().change_view(request, object_id, form_url, extra_context)

if not admin.site.is_registered(ChatMessage):
    admin.site.register(ChatMessage, ChatMessageAdmin)