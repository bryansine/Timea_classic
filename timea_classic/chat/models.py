from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatMessage(models.Model):
    # Added tenant reference for multi-tenancy isolation
    tenant = models.ForeignKey(
        'tenancy.Tenant', 
        on_delete=models.CASCADE, 
        related_name='chat_messages', 
        null=True, 
        blank=True
    )
    
    room_name = models.CharField(max_length=255)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.tenant}] [{self.room_name}] {self.sender.username}: {self.message[:30]}"