from django.db import models
from django.conf import settings

class Tenant(models.Model):
    name = models.CharField(max_length=100, help_text="The name of the business/shop.")
    slug = models.SlugField(unique=True, help_text="Used in the URL pattern to identify this specific shop environment.")
    
    # The merchant/owner who bought or runs this instance
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='owned_shops'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.slug})"