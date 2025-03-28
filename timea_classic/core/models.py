from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    

class Promotion(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='promotions/', blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    promotion_type = models.CharField(
        max_length=10,
        choices=[('banner', 'Banner'), ('popup', 'Pop-up')],
        default='banner'
    )
    location = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., homepage, category_page, product_detail"
    )
    frequency = models.IntegerField(default=1, help_text="For pop-ups, how often to show")

    def __str__(self):
        return self.title